// icons per frame type
const icons = {
  agent: "mdi-account-switch",
  object: "mdi-account-arrow-left-outline",
  action: "mdi-gesture-tap",
  duty: "mdi-exclamation",
  condition: "mdi-circle-small",
  act: "mdi-autorenew",
  claim_duty: "mdi-square",
  nlp: "mdi-text-recognition",
};

// colors per frame type / frame subtype
const colors = {
  fact: "primary",
  agent: "accent",
  object: "amber-10",
  action: "secondary",
  duty: "info",
  condition: "positive",
  multiple: "blue-grey-7",
  act: "deep-purple-10",
  claim_duty: "pink-14"
};

//used for underlining
const hexColors = {
  fact: "#1B2A4A",
  agent: "#C7963E",
  object: "#D47A1A",
  action: "#3A7CA5",
  duty: "#0277BD",
  condition: "#2E7D32",
  multiple: "#546E7A",
  act: "#4527A0",
  claim_duty: "#AD1457",
};

//used for highlighting source text and for node colors in network
const hexColorsLight = {
  fact: "#C8D4E8",
  agent: "#F2E0BA",
  object: "#F5D4B0",
  action: "#B8DAE9",
  duty: "#B3E0F7",
  condition: "#B8E6C0",
  multiple: "#C5D1D5",
  act: "#D1C4F7",
  claim_duty: "#F5B8D4",
  list: "#E2E6EC",
  booleanConstruct: "#E2E6EC"
};

//used for sizing nodes in network
const nodeSizes = {
  fact: 5,
  act: 10,
  claim_duty: 10,
  anonymous: 3
}

export { icons, colors, hexColors, hexColorsLight, nodeSizes };
