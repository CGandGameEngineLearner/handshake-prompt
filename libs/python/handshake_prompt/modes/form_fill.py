# encoding=utf-8
"""
Form-fill mode handler — schema validation, field ownership, missing-field detection.

This is an optional application-layer plugin on top of the core HPP transport.
"""
import time


class FormFillHandler:
  """Handler for mode='form-fill' — AI-assisted form filling with user protection."""

  def setup_session(self, sess, body):
    sess.schema = body.get('schema') or []
    for key, val in (body.get('context') or {}).items():
      by = 'user' if val not in (None, '', [], {}) else 'empty'
      sess.values[key] = {'value': val, 'by': by, 'at': sess._now_iso()}

  def context_response(self, sess):
    return {
      'sessionId': sess.sid,
      'mode':      sess.mode,
      'schema':    sess.schema,
      'context':   sess.get_context(),
      'missing':   sess.get_missing(),
      'meta':      sess.meta,
      'expiresIn': sess.expires_in(),
    }

  def process_actions(self, sess, actions, stream, interval, on_action_callbacks, broadcast):
    applied, rejected, errors = [], [], []

    for act in actions:
      if act.get('type') != 'set':
        errors.append({'action': act, 'msg': 'unsupported action type'})
        continue

      key = act.get('key')
      value = act.get('value')
      if key is None:
        errors.append({'action': act, 'msg': 'missing key'})
        continue

      veto = False
      for cb in on_action_callbacks:
        try:
          if cb(sess, act, None) is False:
            veto = True
            break
        except Exception as e:
          errors.append({'key': key, 'msg': str(e)})
          veto = True
          break
      if veto:
        rejected.append(key)
        continue

      ok, msg = sess.validate_value(key, value)
      if not ok:
        errors.append({'key': key, 'msg': msg})
        continue

      ok = sess.set_value(key, value, 'ai')
      if not ok:
        rejected.append(key)
        continue

      applied.append(key)
      if stream:
        broadcast({'type': 'action', 'key': key, 'value': value})
        if interval > 0:
          time.sleep(interval)

    extra = {'missing': sess.get_missing(), 'context': sess.get_context()}
    return applied, rejected, errors, extra

  def process_notify(self, sess, key, value):
    return sess.set_value(key, value, 'user')

  def process_ws_message(self, sess, msg):
    if msg.get('type') == 'userEdit':
      key = msg.get('key')
      if key is not None:
        self.process_notify(sess, key, msg.get('value'))
