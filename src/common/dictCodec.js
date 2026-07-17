const BASE36_DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"
const BASE64URL_DIGITS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

function parseBase36(value) {
  if (typeof value !== "string" || !/^[0-9a-z]+$/.test(value)) {
    return -1
  }
  let result = 0
  for (let i = 0; i < value.length; i++) {
    const digit = BASE36_DIGITS.indexOf(value.charAt(i))
    if (digit < 0) {
      return -1
    }
    result = result * 36 + digit
    if (result > 9007199254740991) {
      return -1
    }
  }
  return result
}

function decodePrefixField(value, previous) {
  if (typeof value !== "string" || !value || typeof previous !== "string") {
    return null
  }
  const prefixLength = BASE36_DIGITS.indexOf(value.charAt(0))
  if (prefixLength < 0 || prefixLength > previous.length) {
    return null
  }
  return previous.slice(0, prefixLength) + value.slice(1)
}

function decodeBase64Bytes(value) {
  if (typeof value !== "string" || !value || !/^[A-Za-z0-9_-]+$/.test(value) || value.length % 4 === 1) {
    return null
  }

  const bytes = []
  let accumulator = 0
  let bitCount = 0
  for (let i = 0; i < value.length; i++) {
    const digit = BASE64URL_DIGITS.indexOf(value.charAt(i))
    if (digit < 0) {
      return null
    }
    accumulator = accumulator * 64 + digit
    bitCount += 6
    while (bitCount >= 8) {
      bitCount -= 8
      const divisor = Math.pow(2, bitCount)
      bytes.push(Math.floor(accumulator / divisor) & 0xff)
      accumulator %= divisor
    }
  }
  if (bitCount > 0 && (accumulator & ((1 << bitCount) - 1)) !== 0) {
    return null
  }
  return bytes
}

function decodeDeltaIds(value) {
  const bytes = decodeBase64Bytes(value)
  if (!bytes) {
    return []
  }

  const ids = []
  let current = 0
  let delta = 0
  let shift = 0
  for (let i = 0; i < bytes.length; i++) {
    const byte = bytes[i]
    const payload = byte & 0x7f
    if (shift > 53 || (shift === 53 && payload > 1)) {
      return []
    }
    delta += payload * Math.pow(2, shift)
    if (byte & 0x80) {
      shift += 7
      continue
    }
    current += delta
    if (ids.length > 0 && current <= ids[ids.length - 1]) {
      return []
    }
    if (current < 0 || current > 14941) {
      return []
    }
    ids.push(current)
    delta = 0
    shift = 0
  }
  if (shift !== 0 || ids.length === 0) {
    return []
  }
  return ids
}

function parseInflectionValue(value) {
  if (typeof value !== "string" || !value) {
    return null
  }
  if (value.charAt(0) === "@") {
    const entryId = parseBase36(value.slice(1))
    return entryId >= 0 ? {entryId: entryId} : null
  }
  return {word: value}
}

export {decodeDeltaIds, decodePrefixField, parseBase36, parseInflectionValue}
