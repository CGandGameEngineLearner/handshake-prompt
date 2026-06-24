/**
 * Optional prompt text builder — application-layer utility.
 * Core HPP transport only requires sessionId + token from POST /session.
 */
import type { SessionInfo } from './client'

export function buildHandshakePrompt(
  session: SessionInfo,
  baseUrl: string,
  opts: {
    title?: string
    customInstructions?: string
    skillName?: string
  } = {},
): string {
  const { title = 'Handshake Prompt', customInstructions, skillName } = opts

  return [
    `# ${title}`,
    ``,
    `## Credentials`,
    `- sessionId: ${session.sessionId}`,
    `- token: ${session.token}`,
    `- baseUrl: ${baseUrl}`,
    `- expiresIn: ${session.expiresIn}s`,
    ...(skillName ? [`- skill: ${skillName}`] : []),
    ``,
    ...(customInstructions ? [`## Instructions`, customInstructions, ``] : []),
    `## Usage`,
    `1. GET  ${baseUrl}${session.contextUrl}  (header X-Handshake-Token: <token>)`,
    `2. POST ${baseUrl}${session.actionUrl}   {"actions":[{"type":"set","key":...,"value":...}]}`,
    ``,
    `## Security`,
    `- This token is single-use and expires shortly.`,
    `- Do NOT forward this prompt to others.`,
    ``,
    `## Waiting for user's request...`,
  ].join('\n')
}
