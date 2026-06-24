# encoding=utf-8
"""
Generic mode handler — opaque key/value context with no schema validation.

Use for device pairing, config push, or any non-form Agent interaction.
"""


class GenericHandler:
  """Pass-through handler for arbitrary modes."""

  def setup_session(self, sess, body):
    sess.data = dict(body.get('context') or body.get('data') or {})

  def context_response(self, sess):
    return {
      'sessionId': sess.sid,
      'mode':      sess.mode,
      'data':      dict(sess.data),
      'meta':      sess.meta,
      'expiresIn': sess.expires_in(),
    }

  def process_actions(self, sess, actions, stream, interval, on_action_callbacks, broadcast):
    applied, rejected, errors = [], [], []

    for act in actions:
      act_type = act.get('type', 'set')
      if act_type != 'set':
        errors.append({'action': act, 'msg': f'unsupported action type: {act_type}'})
        continue

      key = act.get('key')
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

      value = act.get('value')
      old = sess.data.get(key)
      sess.data[key] = value
      sess.record_change(key, old, value, 'agent')
      applied.append(key)
      if stream:
        broadcast({'type': 'action', 'key': key, 'value': value})

    return applied, rejected, errors, {}

  def process_notify(self, sess, key, value):
    sess.data[key] = value
    sess.record_change(key, None, value, 'user')
    return True

  def process_ws_message(self, sess, msg):
    if msg.get('type') == 'userEdit':
      key = msg.get('key')
      if key is not None:
        self.process_notify(sess, key, msg.get('value'))
