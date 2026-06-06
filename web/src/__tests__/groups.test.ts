import { describe, it, expect } from 'vitest'
import { groupsOf } from '../stores/usePanel'
import type { Status } from '../types'

const st = {
  order: ['a', 'b', 'c'],
  runners: {
    a: { group: '视觉' }, b: { group: '信息' }, c: { group: '信息' },
  },
} as unknown as Status

describe('groupsOf', () => {
  it('orders groups by preference and buckets ids', () => {
    const g = groupsOf(st)
    expect(g.names).toEqual(['信息', '视觉'])
    expect(g.map['信息']).toEqual(['b', 'c'])
    expect(g.map['视觉']).toEqual(['a'])
  })
})
