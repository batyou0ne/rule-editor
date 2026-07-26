<template>
  <div class="q-pa-md">
    <q-card flat bordered>
      <q-card-section>
        <div class="text-subtitle1">interactive eFLINT</div>
      </q-card-section>

      <q-separator />

      <q-card-section>
        <div class="text-caption q-mb-xs">Specification</div>
        <EflintEditor v-model="eflintBase" />

        <div class="text-caption q-mt-md q-mb-xs">Scenario</div>
        <EflintEditor v-model="eflintFinal" />

        <div class="text-caption q-mt-md q-mb-xs">Queries</div>
        <EflintEditor v-model="eflintQuery" />
      </q-card-section>

      <q-separator />

      <q-card-section>
        <div class="text-subtitle2 q-mb-xs">REPL</div>
        <div class="text-caption q-mb-sm">Experimental interactive mode (persistent session)</div>

        <div class="row items-center q-gutter-sm q-mb-sm">
          <q-btn
            color="primary"
            label="Start REPL"
            :loading="isStartingRepl"
            :disable="!!replSessionId"
            @click="startReplSession()"
          />
          <q-btn
            flat
            label="Stop REPL"
            :disable="!replSessionId"
            @click="stopReplSession()"
          />
          <div class="text-caption">Session: {{ replSessionId ? 'active' : 'stopped' }}</div>
        </div>

        <div ref="replTerminalScroll" class="repl-terminal q-mb-sm">
          <div
            ref="replTerminal"
            class="repl-terminal-input"
            tabindex="0"
            @click="focusTerminal()"
            @keydown="onTerminalKeydown"
            @paste.prevent="onTerminalPaste"
          >
            <pre class="repl-terminal-content">{{ renderedTerminal }}</pre>
          </div>
        </div>

        <div class="row items-center q-gutter-sm q-mt-sm q-mb-sm">
          <q-btn
            color="primary"
            label="Send"
            :loading="isRunningRepl"
            :disable="!replSessionId || !replBuffer"
            @click="sendReplCommand(replBuffer)"
          />
          <q-btn
            flat
            label="Paste"
            :disable="!replSessionId"
            @click="pasteFromClipboard()"
          />
        </div>
        <div class="text-caption q-mb-sm">Shortcuts: Ctrl+V / Shift+Insert / Paste button (Win+V opens Windows clipboard history)</div>
        <div v-if="replError" class="text-negative q-mt-sm">{{ replError }}</div>
      </q-card-section>
    </q-card>
  </div>
</template>

<script>
import {
  buildReplSessionInputUrl,
  buildReplSessionStartUrl,
  buildReplSessionStopUrl,
} from "../../services/eflintEndpoints.js";
import EflintEditor from "../../components/EflintEditor.vue";
export default {
  name: "ExecuteTaskView",

  components: { EflintEditor },

  data() {
    return {
      replSessionId: "",
      isStartingRepl: false,
      replBuffer: "",
      isRunningRepl: false,
      replTerminalOutput: "",
      replError: "",
    };
  },

  computed: {
    eflintBase: {
      get() { return this.$store.state.executableEflintBase || ""; },
      set(v) { this.$store.state.executableEflintBase = v; },
    },
    eflintFinal: {
      get() { return this.$store.state.executableEflintFinal || ""; },
      set(v) { this.$store.state.executableEflintFinal = v; },
    },
    eflintQuery: {
      get() { return this.$store.state.executableEflintQuery || ""; },
      set(v) { this.$store.state.executableEflintQuery = v; },
    },
    renderedTerminal() {
      if (!this.replTerminalOutput && !this.replSessionId) {
        return "No REPL output yet. Start REPL to begin.";
      }
      const base = this.replTerminalOutput || "";
      if (!this.replSessionId) {
        return base;
      }
      return `${base}> ${this.replBuffer}█`;
    },
  },

  watch: {
    replTerminalOutput() {
      this.scrollTerminalToBottom();
    },
    replBuffer() {
      this.scrollTerminalToBottom();
    },
  },

  methods: {
    focusTerminal() {
      this.$refs.replTerminal?.focus();
    },

    scrollTerminalToBottom() {
      this.$nextTick(() => {
        const scrollEl = this.$refs.replTerminalScroll;
        if (!scrollEl) {
          return;
        }
        scrollEl.scrollTop = scrollEl.scrollHeight;
      });
    },

    onTerminalPaste(event) {
      if (!this.replSessionId) {
        return;
      }

      const pastedText = event?.clipboardData?.getData("text") || "";
      if (!pastedText) {
        return;
      }
      this.replBuffer += pastedText.replace(/\r/g, "");
    },

    async pasteFromClipboard() {
      if (!this.replSessionId || !navigator?.clipboard?.readText) {
        return;
      }
      try {
        const pastedText = await navigator.clipboard.readText();
        if (pastedText) {
          this.replBuffer += pastedText.replace(/\r/g, "");
        }
      } catch {
      }
    },

    onTerminalKeydown(event) {
      if (!this.replSessionId) {
        return;
      }

      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "v") {
        event.preventDefault();
        this.pasteFromClipboard();
        return;
      }

      if (event.shiftKey && event.key === "Insert") {
        event.preventDefault();
        this.pasteFromClipboard();
        return;
      }

      if (event.key === "Enter") {
        event.preventDefault();
        if (this.replBuffer) {
          this.sendReplCommand(this.replBuffer);
        }
        return;
      }

      if (event.key === "Backspace") {
        event.preventDefault();
        this.replBuffer = this.replBuffer.slice(0, -1);
        return;
      }

      if (event.key === "Tab") {
        event.preventDefault();
        this.replBuffer += "  ";
        return;
      }

      if (event.ctrlKey || event.metaKey || event.altKey) {
        return;
      }

      if (event.key.length === 1) {
        event.preventDefault();
        this.replBuffer += event.key;
      }
    },

    appendToRepl(text) {
      if (!text) {
        return;
      }
      const current = this.replTerminalOutput || "";
      this.replTerminalOutput = `${current}${text}`;
    },

    normalizeReplCommand(command) {
      if (!command) {
        return "";
      }

      return command
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter((line) => line.length > 0)
        .join(" ")
        .trim();
    },

    async startReplSession() {
      if (this.replSessionId || this.isStartingRepl) {
        return;
      }

      this.replTerminalOutput = "";
      this.replBuffer = "";
      this.replError = "";
      this.isStartingRepl = true;

      try {
        const url = buildReplSessionStartUrl();
        const resp = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });

        const data = await resp.json().catch(() => ({}));
        if (!resp.ok) {
          const detail = data?.detail || "Failed to start REPL session";
          this.replError = typeof detail === "string" ? detail : JSON.stringify(detail);
          return;
        }

        this.replSessionId = data?.sessionId || "";
        this.appendToRepl(data?.stdout || "");
        this.appendToRepl(data?.stderr || "");
        this.$nextTick(() => this.focusTerminal());
        this.scrollTerminalToBottom();
      } catch (error) {
        this.replError = error?.message || "Failed to start REPL session";
      } finally {
        this.isStartingRepl = false;
      }
    },

    async stopReplSession() {
      if (!this.replSessionId) {
        return;
      }

      const currentSessionId = this.replSessionId;
      this.replSessionId = "";
      this.replBuffer = "";

      try {
        const url = buildReplSessionStopUrl(currentSessionId);
        await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });
      } catch {
      }
    },

    async sendReplCommand(command) {
      if (!this.replSessionId || !command || this.isRunningRepl) {
        return;
      }

      const normalizedCommand = this.normalizeReplCommand(command);
      if (!normalizedCommand) {
        return;
      }

      this.replError = "";
      this.isRunningRepl = true;
      this.replBuffer = "";
      this.appendToRepl(`> ${normalizedCommand}\n`);

      try {
        const url = buildReplSessionInputUrl(this.replSessionId);
        const resp = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ input: normalizedCommand }),
        });

        const data = await resp.json().catch(() => ({}));
        if (!resp.ok) {
          const detail = data?.detail || "REPL execution failed";
          this.replError = typeof detail === "string" ? detail : JSON.stringify(detail);
          return;
        }

        this.appendToRepl(data?.stdout || "");
        this.appendToRepl(data?.stderr || "");
        if (data?.running === false) {
          this.replSessionId = "";
        }
      } catch (error) {
        this.replError = error?.message || "Failed to execute REPL";
      } finally {
        this.isRunningRepl = false;
        this.$nextTick(() => this.focusTerminal());
        this.scrollTerminalToBottom();
      }
    },

  },

  beforeUnmount() {
    if (this.replSessionId) {
      this.stopReplSession();
    }
  },
};
</script>

<style scoped>
.repl-terminal {
  background: #0D1B2A;
  color: #C8D4E8;
  border-radius: 6px;
  border: 1px solid #1B2A4A;
  min-height: 260px;
  max-height: 420px;
  overflow: auto;
  padding: 12px;
}

.repl-terminal-content {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 12px;
  line-height: 1.4;
}

.repl-terminal-input {
  min-height: 236px;
  cursor: text;
  outline: none;
}

.repl-prompt {
  font-family: monospace;
  font-size: 16px;
  color: #111;
}
</style>
