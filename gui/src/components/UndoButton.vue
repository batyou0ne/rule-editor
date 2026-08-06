<template>
  <q-btn
    flat
    dense
    size="sm"
    icon="mdi-undo"
    text-color="white"
    :disable="!canUndo"
    :label="canUndo ? 'Undo' : 'Undo'"
    @click="performUndo"
  >
    <q-tooltip v-if="canUndo">Undo: {{ lastLabel }} (Ctrl+Z)</q-tooltip>
    <q-tooltip v-else>Nothing to undo</q-tooltip>
  </q-btn>
</template>

<script>
import { useQuasar } from "quasar";

export default {
  name: "UndoButton",

  setup() {
    return { $q: useQuasar() };
  },

  computed: {
    stack() {
      return this.$store.state.undoStack || [];
    },
    canUndo() {
      return this.stack.length > 0;
    },
    lastLabel() {
      return this.stack.length ? this.stack[this.stack.length - 1].label : "";
    },
  },

  mounted() {
    window.addEventListener("keydown", this.onKeydown);
  },

  beforeUnmount() {
    window.removeEventListener("keydown", this.onKeydown);
  },

  methods: {
    performUndo() {
      if (!this.canUndo) return;
      const label = this.lastLabel;
      this.$store.commit("performUndo");
      this.$q.notify({
        type: "info",
        message: `Undone: ${label}`,
        timeout: 1500,
        position: "bottom",
      });
    },

    onKeydown(event) {
      const isUndo =
        (event.ctrlKey || event.metaKey) &&
        !event.shiftKey &&
        !event.altKey &&
        event.key.toLowerCase() === "z";
      if (!isUndo) return;

      // Don't hijack undo when the user is editing text (native undo should win)
      const t = event.target;
      const tag = t?.tagName;
      const editable = t?.isContentEditable;
      if (editable || tag === "INPUT" || tag === "TEXTAREA") return;

      event.preventDefault();
      this.performUndo();
    },
  },
};
</script>
