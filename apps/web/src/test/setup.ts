import '@testing-library/jest-dom/vitest'
import { afterEach, beforeEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import { useUi, initialState } from '../state/store'

// jsdom lacks these; cmdk needs them.
class RO { observe() {} unobserve() {} disconnect() {} }
globalThis.ResizeObserver ??= RO as unknown as typeof ResizeObserver
Element.prototype.scrollIntoView ??= () => {}
beforeEach(() => { localStorage.clear(); useUi.setState(initialState()) })
afterEach(() => cleanup())
