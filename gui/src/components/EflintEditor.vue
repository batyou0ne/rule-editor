<template>
  <Codemirror
    :model-value="modelValue"
    :extensions="extensions"
    :disabled="readonly"
    :style="{ height: autoHeight ? 'auto' : '300px' }"
    :autofocus="false"
    :indent-with-tab="true"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<script>
import { Codemirror } from "vue-codemirror";
import { EditorView } from "@codemirror/view";
import { eflintSyntaxExtensions } from "../helpers/eflintLanguage.js";

const theme = EditorView.theme({
  "&": { fontSize: "13px" },
  ".cm-content": { fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" },
  ".cm-scroller": { fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" },
});

export default {
  name: "EflintEditor",

  components: { Codemirror },

  props: {
    modelValue: { type: String, default: "" },
    readonly: { type: Boolean, default: false },
    autoHeight: { type: Boolean, default: true },
  },

  emits: ["update:modelValue"],

  computed: {
    extensions() {
      return [...eflintSyntaxExtensions, theme, EditorView.lineWrapping];
    },
  },
};
</script>
