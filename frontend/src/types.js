// Type definitions as JSDoc comments for better IDE support

/**
 * @typedef {Object} Message
 * @property {'user' | 'assistant'} role
 * @property {string} content
 * @property {string} timestamp
 * @property {ResearchResult} [result]
 */

/**
 * @typedef {Object} ResearchResult
 * @property {string} [clarity_status]
 * @property {string} [clarification_question]
 * @property {SpellcheckResult} [spellcheck_result]
 * @property {ResearchFindings} [research_findings]
 * @property {number} [confidence_score]
 * @property {string} [validation_result]
 * @property {string} [final_answer]
 * @property {Record<string, any>} [agent_outputs]
 * @property {AgentLog[]} [agent_logs]
 * @property {string} [company_name]
 * @property {number} [attempts]
 */

/**
 * @typedef {Object} SpellcheckResult
 * @property {'no_correction' | 'corrected' | 'uncertain'} status
 * @property {string} [original]
 * @property {string} [suggested]
 * @property {number} [confidence]
 */

/**
 * @typedef {Object} ResearchFindings
 * @property {ResearchItem[]} items
 * @property {number} [total_results]
 */

/**
 * @typedef {Object} ResearchItem
 * @property {string} title
 * @property {string} url
 * @property {string} content
 * @property {number} [score]
 */

/**
 * @typedef {Object} AgentLog
 * @property {string} agent
 * @property {'INFO' | 'WARNING' | 'ERROR' | 'DEBUG'} level
 * @property {string} message
 * @property {string} [timestamp]
 */

/**
 * @typedef {Object} AgentStatus
 * @property {string} agent
 * @property {'pending' | 'running' | 'complete' | 'error'} status
 * @property {string} [message]
 * @property {any} [output]
 */

/**
 * @typedef {Object} StreamEvent
 * @property {'start' | 'agent_start' | 'agent_complete' | 'complete' | 'error'} type
 * @property {string} [agent]
 * @property {string} [status]
 * @property {any} [output]
 * @property {ResearchResult} [result]
 * @property {string} [error]
 * @property {string} [session_id]
 */

export {}
