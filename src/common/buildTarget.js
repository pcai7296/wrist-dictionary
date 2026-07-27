var TARGET_ID = "W212"
var TARGET_WIDTH = 212
var TARGET_HEIGHT = 520
var TARGET_PROFILE = "pill-standard"
var TARGET_SHAPE = "pill-shaped"

// if true: process.env.TARGET_ID === "W192" && process.env.TARGET_WIDTH === "192" && process.env.TARGET_HEIGHT === "490"
TARGET_ID = "W192"
TARGET_WIDTH = 192
TARGET_HEIGHT = 490
TARGET_PROFILE = "pill-compact"
TARGET_SHAPE = "pill-shaped"
// endif

// if true: process.env.TARGET_ID === "W336" && process.env.TARGET_WIDTH === "336" && process.env.TARGET_HEIGHT === "336"
TARGET_ID = "W336"
TARGET_WIDTH = 336
TARGET_HEIGHT = 336
TARGET_PROFILE = "rect"
TARGET_SHAPE = "rect"
// endif

// if true: process.env.TARGET_ID === "W432" && process.env.TARGET_WIDTH === "432" && process.env.TARGET_HEIGHT === "432"
TARGET_ID = "W432"
TARGET_WIDTH = 432
TARGET_HEIGHT = 432
TARGET_PROFILE = "rect"
TARGET_SHAPE = "rect"
// endif

// if true: process.env.TARGET_ID === "W466" && process.env.TARGET_WIDTH === "466" && process.env.TARGET_HEIGHT === "466"
TARGET_ID = "W466"
TARGET_WIDTH = 466
TARGET_HEIGHT = 466
TARGET_PROFILE = "circle"
TARGET_SHAPE = "circle"
// endif

export default {
  id: TARGET_ID,
  width: TARGET_WIDTH,
  height: TARGET_HEIGHT,
  profile: TARGET_PROFILE,
  shape: TARGET_SHAPE
}
