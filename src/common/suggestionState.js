// Shared state for English autocomplete suggestions
// Avoids passing seed/suggestions data through component props,
// which can trigger native crashes during DOM creation on Vela

let _seed = ""
let _suggestions = ""
let _callback = null

export function getSuggestionSeed() {
  return _seed
}

export function setSuggestionSeed(v) {
  _seed = v
}

export function getSuggestions() {
  return _suggestions
}

export function setSuggestions(v) {
  _suggestions = v
  if (_callback) {
    _callback(v)
  }
}

export function onSuggestionsChange(cb) {
  _callback = cb
}
