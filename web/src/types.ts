export interface OptSpec {
  key: string
  label: string
  type?: 'text' | 'number' | 'search'
  choices?: [string, string][]
  min?: number
  max?: number
  endpoint?: string
}
export interface Runner {
  name: string
  group: string
  desc: string
  running: boolean
  interval: number
  optspec: OptSpec[]
  options: Record<string, string | number>
  log: string[]
}
export interface Attachment {
  id: string
  type: string
  typeName: string
  host: string
  running: boolean
  optspec: OptSpec[]
  options: Record<string, string | number>
  log: string[]
}
export interface AttachType { type: string; name: string; desc: string }
export interface Status {
  online: boolean
  device: string
  base: { ip?: string; appVer?: string; mcuVer?: string; ssid?: string }
  config: { brightness?: number; volume?: number; timezone?: string }
  apps: { apps?: string[]; count?: number }
  order: string[]
  runners: Record<string, Runner>
  attachTypes: AttachType[]
  attachments: Record<string, Attachment>
}
export interface GeoResult { label: string; value: string }
