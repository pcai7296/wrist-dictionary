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

function readUleb128(bytes, offset, limit) {
  let value = 0
  let shift = 0
  let index = offset
  while (index < limit) {
    const byte = bytes[index]
    const payload = byte & 0x7f
    if (shift > 53 || (shift === 53 && payload > 1)) {
      return null
    }
    value += payload * Math.pow(2, shift)
    index++
    if (!(byte & 0x80)) {
      return {value: value, offset: index}
    }
    shift += 7
  }
  return null
}

function decodeRawDeltaIds(bytes, start, end) {
  const ids = []
  let current = 0
  let offset = start
  while (offset < end) {
    const decoded = readUleb128(bytes, offset, end)
    if (!decoded) return []
    current += decoded.value
    if ((ids.length && current <= ids[ids.length - 1]) || current < 0 || current > 14941) return []
    ids.push(current)
    offset = decoded.offset
  }
  return offset === end && ids.length ? ids : []
}

function decodeUtf8(bytes, start, end) {
  let result = ""
  for (let i = start; i < end; ) {
    const first = bytes[i]
    if (first < 0x80) {
      result += String.fromCharCode(first)
      i++
    } else if (first >= 0xc2 && first <= 0xdf && i + 1 < end && (bytes[i + 1] & 0xc0) === 0x80) {
      result += String.fromCharCode(((first & 0x1f) << 6) | (bytes[i + 1] & 0x3f))
      i += 2
    } else if (first >= 0xe0 && first <= 0xef && i + 2 < end && (bytes[i + 1] & 0xc0) === 0x80 && (bytes[i + 2] & 0xc0) === 0x80) {
      result += String.fromCharCode(((first & 0x0f) << 12) | ((bytes[i + 1] & 0x3f) << 6) | (bytes[i + 2] & 0x3f))
      i += 3
    } else {
      return null
    }
  }
  return result
}

function decodeChineseIndex(bytes, kind) {
  const magic = kind === "cn" ? [87, 68, 67, 52] : [87, 68, 90, 52]
  if (!bytes || bytes.length < 4) return null
  for (let i = 0; i < 4; i++) if (bytes[i] !== magic[i]) return null
  const indexMap = {}
  let offset = 4
  let previous = ""
  while (offset < bytes.length) {
    const first = readUleb128(bytes, offset, bytes.length)
    if (!first) return null
    offset = first.offset
    let phrase = ""
    if (kind === "cn") {
      const suffixLength = readUleb128(bytes, offset, bytes.length)
      if (!suffixLength || first.value > previous.length) return null
      offset = suffixLength.offset
      const suffixEnd = offset + suffixLength.value
      if (suffixEnd > bytes.length) return null
      const suffix = decodeUtf8(bytes, offset, suffixEnd)
      if (suffix === null) return null
      phrase = previous.slice(0, first.value) + suffix
      offset = suffixEnd
    } else {
      const keyEnd = offset + first.value
      if (keyEnd > bytes.length) return null
      phrase = decodeUtf8(bytes, offset, keyEnd)
      if (phrase === null) return null
      offset = keyEnd
    }
    const payloadLength = readUleb128(bytes, offset, bytes.length)
    if (!payloadLength) return null
    offset = payloadLength.offset
    const payloadEnd = offset + payloadLength.value
    if (payloadEnd > bytes.length) return null
    const ids = decodeRawDeltaIds(bytes, offset, payloadEnd)
    if (!ids.length || indexMap[phrase]) return null
    indexMap[phrase] = ids
    previous = phrase
    offset = payloadEnd
  }
  return indexMap
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

export {decodeChineseIndex, decodeDeltaIds, decodePrefixField, parseBase36, parseInflectionValue}
