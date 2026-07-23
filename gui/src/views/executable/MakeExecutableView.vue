<template>
  <div class="q-pa-md">
    <div class="row items-center q-gutter-sm q-mb-md">
      <q-btn color="primary" label="Generate eFLINT" :loading="isGenerating" @click="generateEflint" />
      <q-btn
        v-if="isExpertMode"
        color="primary"
        outline
        label="Reset Session"
        :loading="isResettingSession"
        @click="resetEflintSession"
      />
      <q-btn-dropdown
        v-if="isExpertMode"
        color="primary"
        outline
        label="Export eFLINT"
        :disable="!eflintBase && !eflintFinal"
      >
        <q-list>
          <q-item clickable v-close-popup dense :disable="!eflintBase" @click="exportEflint('specification')">
            <q-item-section>Specification (.eflint)</q-item-section>
          </q-item>
          <q-item clickable v-close-popup dense :disable="!eflintFinal" @click="exportEflint('scenario')">
            <q-item-section>Scenario (.eflint)</q-item-section>
          </q-item>
        </q-list>
      </q-btn-dropdown>
      <q-btn
        color="primary"
        outline
        label="Evaluate Queries"
        :loading="isEvaluatingQueries"
        :disable="!eflintBase"
        @click="evaluateQueries"
      />
      <q-space />
      <q-toggle v-model="isExpertMode" label="Expert mode" />
    </div>

    <div class="row q-col-gutter-md">
      <div class="col-12 col-lg-6">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1">Frames</div>
          </q-card-section>

          <q-separator />

          <q-card-section>
            <q-btn flat label="Select all shown" class="q-mr-sm" @click="selectAll" />
            <q-btn flat label="Select none" @click="selectNone" />

            <q-list bordered separator class="q-mt-md">
              <q-item v-for="f in visibleFrames" :key="f.id">
                <q-item-section avatar>
                  <q-checkbox :model-value="selectedIds.includes(f.id)" @click.stop="toggle(f.id)" />
                </q-item-section>

                <q-item-section class="cursor-pointer" @click="toggle(f.id)">
                  <q-item-label>{{ f.shortName }}</q-item-label>
                  <q-item-label caption>
                    {{ f.typeId === "fact" ? (f.subTypeIds?.[0] || f.typeId) : f.typeId }}
                  </q-item-label>

                  <div v-if="isAgentFact(f) && selectedIds.includes(f.id)" @click.stop class="q-mt-xs">
                    <div
                      v-for="(name, idx) in (agentInstanceNames[f.id] || [])"
                      :key="`${f.id}-${idx}`"
                      class="row items-center q-gutter-sm q-mb-xs"
                    >
                      <q-input
                        dense
                        outlined
                        placeholder="instance name"
                        :model-value="name"
                        @update:model-value="setAgentInstanceName(f.id, idx, $event)"
                        style="flex: 1;"
                      />
                      <q-btn dense flat label="Delete" @click.stop="removeAgentInstance(f.id, idx)" />
                    </div>

                    <q-btn dense flat label="Add instance" @click.stop="addAgentInstance(f.id)" />
                  </div>

                  <div v-if="isAct(f) && selectedIds.includes(f.id)" @click.stop class="q-mt-xs">
                    <q-select
                      dense
                      outlined
                      label="Actor type"
                      :options="agentTypeOptions()"
                      emit-value
                      map-options
                      v-model="actSelections[f.id].actorType"
                      class="q-mb-xs"
                    />
                    <q-select
                      dense
                      outlined
                      label="Actor name"
                      :options="agentNameOptions(actSelections[f.id]?.actorType)"
                      emit-value
                      map-options
                      v-model="actSelections[f.id].actorName"
                      class="q-mb-xs"
                    />
                    <q-select
                      dense
                      outlined
                      label="Recipient type"
                      :options="agentTypeOptions()"
                      emit-value
                      map-options
                      v-model="actSelections[f.id].recipientType"
                      class="q-mb-xs"
                    />
                    <q-select
                      dense
                      outlined
                      label="Recipient name"
                      :options="agentNameOptions(actSelections[f.id]?.recipientType)"
                      emit-value
                      map-options
                      v-model="actSelections[f.id].recipientName"
                      class="q-mb-xs"
                    />
                  </div>
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-lg-6">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1">Queries</div>
          </q-card-section>

          <q-separator />

          <q-card-section>
            <q-btn flat label="Select all shown" class="q-mr-sm" @click="selectAllQueries" />
            <q-btn flat label="Select none" @click="selectNoneQueries" />

            <q-list bordered separator class="q-mt-md">
              <q-item v-for="f in actFrames" :key="`query-${f.id}`" :class="queryItemClass(f.id)">
                <q-item-section avatar>
                  <q-checkbox :model-value="querySelectedIds.includes(f.id)" @click.stop="toggleQuery(f.id)" />
                </q-item-section>

                <q-item-section class="cursor-pointer" @click="toggleQuery(f.id)">
                  <q-item-label>{{ f.shortName }}</q-item-label>
                  <q-item-label caption>query act</q-item-label>

                  <div v-if="querySelectedIds.includes(f.id)" @click.stop class="q-mt-xs">
                    <q-select
                      dense
                      outlined
                      label="Actor type"
                      :options="agentTypeOptions()"
                      emit-value
                      map-options
                      v-model="queryActSelections[f.id].actorType"
                      class="q-mb-xs"
                    />
                    <q-select
                      dense
                      outlined
                      label="Actor name"
                      :options="agentNameOptions(queryActSelections[f.id]?.actorType)"
                      emit-value
                      map-options
                      v-model="queryActSelections[f.id].actorName"
                      class="q-mb-xs"
                    />
                    <q-select
                      dense
                      outlined
                      label="Recipient type"
                      :options="agentTypeOptions()"
                      emit-value
                      map-options
                      v-model="queryActSelections[f.id].recipientType"
                      class="q-mb-xs"
                    />
                    <q-select
                      dense
                      outlined
                      label="Recipient name"
                      :options="agentNameOptions(queryActSelections[f.id]?.recipientType)"
                      emit-value
                      map-options
                      v-model="queryActSelections[f.id].recipientName"
                      class="q-mb-xs"
                    />
                  </div>
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>
      </div>

      <div v-if="isExpertMode" class="col-12">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1">eFLINT</div>
          </q-card-section>

          <q-separator />

          <q-card-section>
            <q-expansion-item default-opened header-class="text-caption" label="Specification">
              <div class="q-pt-sm">
                <q-input
                  v-model="eflintBase"
                  type="textarea"
                  autogrow
                  outlined
                  input-style="font-family: monospace;"
                />
                <div class="row items-center q-gutter-sm q-mt-sm">
                  <q-btn
                    color="primary"
                    outline
                    label="Run Specification"
                    :loading="isRunningSpecification"
                    :disable="!eflintBase"
                    @click="runSpecification"
                  />
                </div>
              </div>
            </q-expansion-item>

            <q-expansion-item default-opened header-class="text-caption q-mt-md" label="Run Specification Output">
              <div class="q-pt-sm">
                <q-input
                  :model-value="specificationExecutionOutput"
                  type="textarea"
                  autogrow
                  outlined
                  readonly
                  input-style="font-family: monospace;"
                />
              </div>
            </q-expansion-item>

            <q-expansion-item default-opened header-class="text-caption q-mt-md" label="Scenario">
              <div class="q-pt-sm">
                <q-input
                  v-model="eflintFinal"
                  type="textarea"
                  autogrow
                  outlined
                  input-style="font-family: monospace;"
                />
                <div class="row items-center q-gutter-sm q-mt-sm">
                  <q-btn
                    color="primary"
                    outline
                    label="Run Scenario"
                    :loading="isRunningScenario"
                    :disable="!eflintFinal"
                    @click="runScenario"
                  />
                </div>
              </div>
            </q-expansion-item>

            <q-expansion-item default-opened header-class="text-caption q-mt-md" label="Run Scenario Output">
              <div class="q-pt-sm">
                <q-input
                  :model-value="scenarioExecutionOutput"
                  type="textarea"
                  autogrow
                  outlined
                  readonly
                  input-style="font-family: monospace;"
                />
              </div>
            </q-expansion-item>

            <q-expansion-item default-opened header-class="text-caption q-mt-md" label="Queries">
              <div class="q-pt-sm">
                <q-input
                  v-model="eflintQuery"
                  type="textarea"
                  autogrow
                  outlined
                  input-style="font-family: monospace;"
                />
                <div class="row items-center q-gutter-sm q-mt-sm">
                  <q-btn
                    color="primary"
                    outline
                    label="Run Queries"
                    :loading="isRunningQueries"
                    :disable="!eflintQuery"
                    @click="runQueries"
                  />
                </div>
              </div>
            </q-expansion-item>

            <q-expansion-item default-opened header-class="text-caption q-mt-md" label="Run Queries Output">
              <div class="q-pt-sm">
                <q-input
                  :model-value="evaluationOutput"
                  type="textarea"
                  autogrow
                  outlined
                  readonly
                  input-style="font-family: monospace;"
                />
              </div>
            </q-expansion-item>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </div>
</template>

<script>
import { convertInterpretationToJson } from "../../helpers/importExport.js";
import { alertWidget } from "../../helpers/alertWidget.js";
import { buildEflintApiUrl } from "../../services/AuthService.js";
import { buildEflintServerUrl } from "../../services/eflintEndpoints.js";

export default {
  name: "MakeExecutableView",

  data() {
    return {
      isGenerating: false,
      isResettingSession: false,
      isRunningSpecification: false,
      isRunningScenario: false,
      isRunningQueries: false,
      isEvaluatingQueries: false,
      isExpertMode: false,
      eflintServerSessionId: "",
      evaluationOutput: "",
      specificationExecutionOutput: "",
      scenarioExecutionOutput: "",
      queryExecutionStatusByFrame: {},
    };
  },

  computed: {
    selectedIds: {
      get() { return this.$store.state.executableSelectedIds || []; },
      set(v) { this.$store.state.executableSelectedIds = v; },
    },

    clickOrder: {
      get() { return this.$store.state.executableClickOrder || []; },
      set(v) { this.$store.state.executableClickOrder = v; },
    },

    agentInstanceNames: {
      get() { return this.$store.state.executableAgentInstanceNames || {}; },
      set(v) { this.$store.state.executableAgentInstanceNames = v; },
    },

    actSelections: {
      get() { return this.$store.state.executableActSelections || {}; },
      set(v) { this.$store.state.executableActSelections = v; },
    },

    querySelectedIds: {
      get() { return this.$store.state.executableQuerySelectedIds || []; },
      set(v) { this.$store.state.executableQuerySelectedIds = v; },
    },

    queryClickOrder: {
      get() { return this.$store.state.executableQueryClickOrder || []; },
      set(v) { this.$store.state.executableQueryClickOrder = v; },
    },

    queryActSelections: {
      get() { return this.$store.state.executableQueryActSelections || {}; },
      set(v) { this.$store.state.executableQueryActSelections = v; },
    },

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

    allFrames() {
      const a = this.$store.state.frames || [];
      const b = this.$store.state.framesOpenInEditor || [];
      const byId = new Map();
      [...a, ...b].forEach((f) => {
        if (f && f.id) byId.set(f.id, f);
      });
      return [...byId.values()];
    },

    framesUnion() {
      const rank = (f) => {
        if (f.typeId === "fact") {
          if (f.subTypeIds?.[0] === "agent") return 0;
          if (f.subTypeIds?.[0] === "object") return 1;
          if (f.subTypeIds?.[0] === "condition") return 2;
          return 3;
        }
        if (f.typeId === "act") return 4;
        return 9;
      };

      return this.allFrames
        .filter((f) => !(f.typeId === "fact" && ["action"].includes(f.subTypeIds?.[0])))
        .slice()
        .sort((a, b) => {
          const ra = rank(a), rb = rank(b);
          if (ra !== rb) return ra - rb;
          return a.shortName.localeCompare(b.shortName);
        });
    },

    actFrames() {
      return this.framesUnion.filter((f) => this.isAct(f));
    },

    visibleFrames() {
      return this.framesUnion.filter((f) => !this.isAct(f));
    },

    selectedFrames() {
      const byId = Object.fromEntries(this.framesUnion.map((f) => [f.id, f]));
      const seen = new Set();
      const out = [];

      for (const id of this.clickOrder) {
        if (!this.selectedIds.includes(id)) continue;
        if (!byId[id]) continue;
        if (seen.has(id)) continue;
        seen.add(id);
        out.push(byId[id]);
      }

      return out;
    },

    querySelectedFrames() {
      const byId = Object.fromEntries(this.actFrames.map((f) => [f.id, f]));
      const seen = new Set();
      const out = [];

      for (const id of this.queryClickOrder) {
        if (!this.querySelectedIds.includes(id)) continue;
        if (!byId[id]) continue;
        if (seen.has(id)) continue;
        seen.add(id);
        out.push(byId[id]);
      }

      return out;
    },

    scenarioSelectionLines() {
      return this.selectedFrames
        .map((f) => {
          if (this.isAgentFact(f)) {
            const names = this.agentInstanceNames[f.id] || [];
            return names
              .filter((n) => String(n).trim().length > 0)
              .map((n) => `+[${f.shortName}]("${this.escape(n)}") .`)
              .join("\n");
          }

          if (this.isAct(f)) {
            return `+${this.buildActTerm(f, this.actSelections[f.id] || {})} .`;
          }

          return `+[${f.shortName}] .`;
        })
        .join("\n")
        .split("\n")
        .filter((l) => l.trim().length > 0);
    },

    queryResultLines() {
      return this.querySelectedFrames
        .map((f) => `?Enabled(${this.buildActTerm(f, this.queryActSelections[f.id] || {})}).`);
    },

    queryResultText() {
      if (!this.queryResultLines.length) {
        return this.eflintQuery || "";
      }
      return this.normalizeEflint(`${this.queryResultLines.join("\n")}\n`);
    },

    selectionLines() {
      return [...this.scenarioSelectionLines, ...this.queryResultLines];
    },
  },

  watch: {
    scenarioSelectionLines: {
      handler(lines) {
        this.eflintFinal = lines.length
          ? this.normalizeEflint(`${lines.join("\n")}\n`)
          : "";
      },
      deep: true,
      immediate: true,
    },
    queryResultText: {
      handler(value) {
        this.eflintQuery = value || "";
      },
      immediate: true,
    },
  },

  methods: {
    agentTypeOptions() {
      return this.framesUnion
        .filter((f) => this.isAgentFact(f))
        .map((f) => ({ label: f.shortName, value: f.id }));
    },

    agentNameOptions(typeId) {
      return (this.agentInstanceNames[typeId] || []).map((name) => ({ label: name, value: name }));
    },

    findFrameById(id) {
      return this.framesUnion.find((f) => f.id === id) || this.allFrames.find((f) => f.id === id) || null;
    },

    inferredActSelection(f) {
      const actorType = f?.actor?.id || "";
      const recipientType = f?.recipient?.id || "";
      const actorFrame = this.findFrameById(actorType);
      const recipientFrame = this.findFrameById(recipientType);

      return {
        actorType,
        actorName: actorFrame ? this.defaultAgentInstanceName(actorFrame) : "",
        recipientType,
        recipientName: recipientFrame ? this.defaultAgentInstanceName(recipientFrame) : "",
      };
    },

    ensureAgentTypeHasDefaultName(typeId) {
      if (!typeId) return;
      if (this.agentInstanceNames[typeId] !== undefined) return;
      const frame = this.findFrameById(typeId);
      if (!frame || !this.isAgentFact(frame)) return;
      this.agentInstanceNames = {
        ...this.agentInstanceNames,
        [typeId]: [this.defaultAgentInstanceName(frame)],
      };
    },

    buildActTerm(f, selection) {
      const actorFrame = this.findFrameById(selection.actorType || f.actor?.id);
      const recipientFrame = this.findFrameById(selection.recipientType || f.recipient?.id);
      const at = actorFrame?.shortName || f.actor?.shortName || "";
      const rt = recipientFrame?.shortName || f.recipient?.shortName || "";
      const an = this.escape(selection.actorName || "");
      const rn = this.escape(selection.recipientName || "");
      return `[${f.shortName}]([${at}]("${an}"), [${rt}]("${rn}"))`;
    },


    normalizeEflint(text) {
      // Newlines are only allowed directly after a full stop.
      // Any newline (including blank lines) that interrupts a statement is collapsed into a space.
      const lines = text.split('\n');
      const out = [];
      let buffer = '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed === '') {
          // Blank line: only emit as a separator when we are NOT mid-statement.
          // If we are mid-statement (buffer not ending with '.'), absorb the blank line.
          if (buffer === '') {
            out.push('');
          }
          // else: mid-statement blank line — skip it, keep accumulating
        } else {
          buffer = buffer === '' ? trimmed : buffer + ' ' + trimmed;
          if (buffer.endsWith('.')) { out.push(buffer); buffer = ''; }
        }
      }

      if (buffer !== '') out.push(buffer);
      return out.join('\n');
    },

    defaultAgentInstanceName(f) {
      return f.shortName.trim().replace(/\s+/g, "_") + "_1";
    },

    isAgentFact(f) {
      return f.typeId === "fact" && f.subTypeIds?.[0] === "agent";
    },

    isAct(f) {
      return f.typeId === "act";
    },

    escape(s) {
      return String(s).replace(/\\/g, "\\\\").replace(/"/g, '\\"');
    },

    addAgentInstance(agentId) {
      const cur = this.agentInstanceNames[agentId] || [];
      this.agentInstanceNames = {
        ...this.agentInstanceNames,
        [agentId]: [...cur, ""],
      };
    },

    removeAgentInstance(agentId, idx) {
      const cur = this.agentInstanceNames[agentId] || [];
      const next = cur.filter((_, i) => i !== idx);
      this.agentInstanceNames = {
        ...this.agentInstanceNames,
        [agentId]: next.length ? next : [""],
      };
    },

    setAgentInstanceName(agentId, idx, value) {
      const cur = this.agentInstanceNames[agentId] || [];
      const next = cur.slice();
      next[idx] = value;
      this.agentInstanceNames = {
        ...this.agentInstanceNames,
        [agentId]: next,
      };
    },

    toggle(id) {
      if (this.selectedIds.includes(id)) {
        this.selectedIds = this.selectedIds.filter((x) => x !== id);
        this.clickOrder = this.clickOrder.filter((x) => x !== id);
        return;
      }

      this.selectedIds = [...this.selectedIds, id];
      this.clickOrder = [...this.clickOrder, id];

      const f = this.framesUnion.find((x) => x.id === id);

      if (f && this.isAgentFact(f) && this.agentInstanceNames[id] === undefined) {
        this.agentInstanceNames = { ...this.agentInstanceNames, [id]: [this.defaultAgentInstanceName(f)] };
      }

      if (f && this.isAct(f) && this.actSelections[id] === undefined) {
        const inferred = this.inferredActSelection(f);
        this.ensureAgentTypeHasDefaultName(inferred.actorType);
        this.ensureAgentTypeHasDefaultName(inferred.recipientType);
        this.actSelections = {
          ...this.actSelections,
          [id]: inferred,
        };
      }
    },

    toggleQuery(id) {
      if (this.querySelectedIds.includes(id)) {
        this.querySelectedIds = this.querySelectedIds.filter((x) => x !== id);
        this.queryClickOrder = this.queryClickOrder.filter((x) => x !== id);
        return;
      }

      this.querySelectedIds = [...this.querySelectedIds, id];
      this.queryClickOrder = [...this.queryClickOrder, id];

      const f = this.actFrames.find((x) => x.id === id);
      if (!f || this.queryActSelections[id] !== undefined) return;

      const inferred = this.inferredActSelection(f);
      this.ensureAgentTypeHasDefaultName(inferred.actorType);
      this.ensureAgentTypeHasDefaultName(inferred.recipientType);
      this.queryActSelections = {
        ...this.queryActSelections,
        [id]: inferred,
      };
    },

    selectAll() {
      const visibleIds = this.visibleFrames.map((f) => f.id);
      const hiddenActIds = this.selectedIds.filter((id) => {
        const frame = this.framesUnion.find((f) => f.id === id);
        return frame && this.isAct(frame);
      });

      this.selectedIds = [...new Set([...hiddenActIds, ...visibleIds])];
      this.clickOrder = [...hiddenActIds.filter((id) => this.selectedIds.includes(id)), ...visibleIds];

      const names = { ...this.agentInstanceNames };
      const acts = { ...this.actSelections };

      this.visibleFrames.forEach((f) => {
        if (this.isAgentFact(f) && names[f.id] === undefined) names[f.id] = [this.defaultAgentInstanceName(f)];
        if (this.isAct(f) && acts[f.id] === undefined) {
          acts[f.id] = this.inferredActSelection(f);
          this.ensureAgentTypeHasDefaultName(acts[f.id].actorType);
          this.ensureAgentTypeHasDefaultName(acts[f.id].recipientType);
        }
      });

      this.agentInstanceNames = names;
      this.actSelections = acts;
    },

    selectAllQueries() {
      this.querySelectedIds = this.actFrames.map((f) => f.id);
      this.queryClickOrder = [...this.querySelectedIds];

      const queryActs = { ...this.queryActSelections };
      this.actFrames.forEach((f) => {
        if (queryActs[f.id] === undefined) {
          queryActs[f.id] = this.inferredActSelection(f);
          this.ensureAgentTypeHasDefaultName(queryActs[f.id].actorType);
          this.ensureAgentTypeHasDefaultName(queryActs[f.id].recipientType);
        }
      });

      this.queryActSelections = queryActs;
    },

    selectNoneQueries() {
      this.querySelectedIds = [];
      this.queryClickOrder = [];
    },

    selectNone() {
      const visibleIds = new Set(this.visibleFrames.map((f) => f.id));
      this.selectedIds = this.selectedIds.filter((id) => !visibleIds.has(id));
      this.clickOrder = this.clickOrder.filter((id) => !visibleIds.has(id));
    },

    sanitizeFilePart(value) {
      return String(value || "")
        .trim()
        .replace(/\s+/g, "-")
        .replace(/[^a-zA-Z0-9-_]/g, "")
        .slice(0, 50);
    },

    buildEflintFilename(kind) {
      const dateString = new Date().toISOString().substring(0, 19).replace(/[:T]/g, "-");
      const taskLabel = this.sanitizeFilePart(this.$store.state.task?.label) || "task";
      return `${dateString}_${taskLabel}_${kind}.eflint`;
    },

    downloadTextFile(content, fileName, mimeType = "text/plain;charset=utf-8") {
      const blob = new Blob([content], { type: mimeType });
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(objectUrl);
    },

    exportEflint(kind) {
      const content = kind === "scenario" ? this.eflintFinal : this.eflintBase;
      if (!content) return;
      const fileName = this.buildEflintFilename(kind);
      this.downloadTextFile(content, fileName, "application/octet-stream;charset=utf-8");
    },

    async generateEflint() {
      this.isGenerating = true;

      try {
        const interpretation = convertInterpretationToJson(
          this.$store.state.task,
          this.allFrames,
          this.$store.state.sourceDocuments || []
        );

        const resp = await fetch(buildEflintApiUrl("/generate-eflint"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ interpretation }),
        });

        const data = await resp.json();
        const eflint = data?.eflint || "";

        this.eflintBase = this.normalizeEflint(eflint);
      } finally {
        this.isGenerating = false;
      }
    },

    async ensureEflintServerSession() {
      if (this.eflintServerSessionId) {
        return this.eflintServerSessionId;
      }

      return this.createEflintServerSession();
    },

    async createEflintServerSession() {

      const resp = await fetch(buildEflintServerUrl("/sessions"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });

      const text = await resp.text();
      let data = {};
      try {
        data = text ? JSON.parse(text) : {};
      } catch {
      }

      if (!resp.ok) {
        const detail = data?.detail || data?.error || text || resp.statusText;
        throw new Error(`Session creation failed (${resp.status}): ${detail}`);
      }

      const sessionId = data?.session_id;
      if (!sessionId) {
        throw new Error("Session creation failed: missing session_id in response");
      }

      this.eflintServerSessionId = sessionId;
      return sessionId;
    },

    async recreateEflintServerSession() {
      const previousSessionId = this.eflintServerSessionId;

      if (previousSessionId) {
        const deleteResp = await fetch(
          buildEflintServerUrl(`/sessions/${encodeURIComponent(previousSessionId)}`),
          { method: "DELETE" },
        );

        if (!deleteResp.ok && deleteResp.status !== 404) {
          const deleteText = await deleteResp.text();
          throw new Error(
            `Reset failed while deleting session (${deleteResp.status}): ${deleteText || deleteResp.statusText}`,
          );
        }
      }

      return this.createEflintServerSession();
    },

    extractHoldQueries(text) {
      return this.normalizeEflint(text || "")
        .split("\n")
        .map((line) => line.trim())
        .filter((line) => line.length > 0)
        .filter((line) => line.startsWith("?Enabled("));
    },

    queryItemClass(frameId) {
      const status = this.queryExecutionStatusByFrame[frameId];
      if (status === "positive") return "bg-green-1";
      if (status === "negative") return "bg-red-1";
      if (status === "error") return "bg-grey-4";
      return "";
    },

    async parseEflintResponse(resp) {
      const responseText = await resp.text();
      let data = {};
      try {
        data = responseText ? JSON.parse(responseText) : {};
      } catch {
        data = { raw: responseText };
      }
      return { data, responseText };
    },

    isSuccessfulEflintResult(resp, data) {
      return !!resp?.ok && data?.response === "success" && Array.isArray(data?.errors) && data.errors.length === 0;
    },

    getEflintErrorDetail(resp, data, responseText, fallbackLabel) {
      return data?.detail || data?.error || responseText || resp?.statusText || fallbackLabel;
    },

    normalizeQueryStatus(result) {
      // Grey if there are errors
      if (Array.isArray(result?.errors) && result.errors.length > 0) {
        return "error";
      }

      const queryResults = Array.isArray(result?.["query-results"]) ? result["query-results"] : [];

      // Green if any entry in query-results indicates success, red otherwise
      const hasPositive = queryResults.some((entry) => {
        if (entry === true) return true;
        if (entry === false || entry == null) return false;
        if (typeof entry === "string") {
          const normalized = entry.trim().toLowerCase();
          return normalized === "true" || normalized === "success";
        }
        if (typeof entry === "number") return entry !== 0;
        if (Array.isArray(entry)) return entry.length > 0;
        if (typeof entry === "object") {
          if ("result" in entry) return Boolean(entry.result);
          if ("value" in entry) return Boolean(entry.value);
          if ("response" in entry) {
            const normalized = String(entry.response).trim().toLowerCase();
            return normalized === "true" || normalized === "success";
          }
          return true;
        }
        return Boolean(entry);
      });
      return hasPositive ? "positive" : "negative";
    },

    async softResetEflintState(sessionId) {
      const headers = {
        "Content-Type": "application/json",
        "X-Session-Id": sessionId,
      };
      const resp = await fetch(buildEflintServerUrl("/reset"), {
        method: "POST",
        headers,
        body: JSON.stringify({ value: -1, destructive: true }),
      });
      const { data, responseText } = await this.parseEflintResponse(resp);
      // "invalid state" means there is nothing to revert (fresh session) — treat as success
      const isInvalidState = data && data.response === "invalid state";
      if (!isInvalidState && !this.isSuccessfulEflintResult(resp, data)) {
        const detail = this.getEflintErrorDetail(resp, data, responseText, "Reset failed");
        throw new Error(`Reset failed (${resp.status}): ${detail}`);
      }
      return data;
    },

    async executeSpecification(sessionId) {
      const headers = {
        "Content-Type": "application/json",
        "X-Session-Id": sessionId,
      };
      const resp = await fetch(buildEflintServerUrl("/spec/register"), {
        method: "POST",
        headers,
        body: JSON.stringify({ text: this.eflintBase || "" }),
      });
      const { data, responseText } = await this.parseEflintResponse(resp);
      this.specificationExecutionOutput = JSON.stringify({ session_id: sessionId, specification_result: data }, null, 2);
      return { resp, data, responseText };
    },

    async executeScenario(sessionId) {
      const headers = {
        "Content-Type": "application/json",
        "X-Session-Id": sessionId,
      };
      const resp = await fetch(buildEflintServerUrl("/statements"), {
        method: "POST",
        headers,
        body: JSON.stringify({ text: this.eflintFinal || "" }),
      });
      const { data, responseText } = await this.parseEflintResponse(resp);
      this.scenarioExecutionOutput = JSON.stringify({ session_id: sessionId, scenario_result: data }, null, 2);
      return { resp, data, responseText };
    },

    buildQueryFramePairs() {
      const queries = this.extractHoldQueries(this.eflintQuery);
      return queries.map((query, index) => ({
        frameId: this.querySelectedFrames[index]?.id || null,
        query,
      }));
    },

    async resetEflintSession() {
      this.isResettingSession = true;
      try {
        const newSessionId = await this.recreateEflintServerSession();

        this.specificationExecutionOutput = "";
        this.scenarioExecutionOutput = "";
        this.evaluationOutput = "";
        alertWidget("success", `eFLINT session reset successfully (${newSessionId}).`);
      } catch (error) {
        alertWidget("error", error?.message || "Session reset failed");
      } finally {
        this.isResettingSession = false;
      }
    },

    async runSpecification() {
      this.isRunningSpecification = true;
      try {
        const sessionId = await this.ensureEflintServerSession();
        await this.softResetEflintState(sessionId);
        const { resp, data, responseText } = await this.executeSpecification(sessionId);
        if (!this.isSuccessfulEflintResult(resp, data)) {
          const detail = this.getEflintErrorDetail(resp, data, responseText, "Specification execution failed");
          throw new Error(`Specification execution failed (${resp.status}): ${detail}`);
        }
      } catch (error) {
        this.specificationExecutionOutput = error?.message || "Specification execution failed";
      } finally {
        this.isRunningSpecification = false;
      }
    },

    async runScenario() {
      this.isRunningScenario = true;
      try {
        const sessionId = await this.ensureEflintServerSession();
        const { resp, data, responseText } = await this.executeScenario(sessionId);
        if (!this.isSuccessfulEflintResult(resp, data)) {
          const detail = this.getEflintErrorDetail(resp, data, responseText, "Scenario execution failed");
          throw new Error(`Scenario execution failed (${resp.status}): ${detail}`);
        }
      } catch (error) {
        this.scenarioExecutionOutput = error?.message || "Scenario execution failed";
      } finally {
        this.isRunningScenario = false;
      }
    },

    async runQueries() {
      this.isRunningQueries = true;
      this.evaluationOutput = "";
      this.queryExecutionStatusByFrame = {};

      try {
        const queryPairs = this.buildQueryFramePairs();
        if (!queryPairs.length) {
          throw new Error("No ?Enabled(...) queries found to execute");
        }

        const sessionId = await this.ensureEflintServerSession();
        const headers = {
          "Content-Type": "application/json",
          "X-Session-Id": sessionId,
        };

        const results = [];
        const statusByFrame = {};

        for (const { frameId, query } of queryPairs) {
          const resp = await fetch(buildEflintServerUrl("/query/enabled"), {
            method: "POST",
            headers,
            body: JSON.stringify({ text: query }),
          });

          const { data, responseText } = await this.parseEflintResponse(resp);
          const ok = resp?.ok;
          const status = ok ? this.normalizeQueryStatus(data) : "";
          if (status) {
            statusByFrame[frameId] = status;
          }

          if (!ok) {
            const detail = this.getEflintErrorDetail(resp, data, responseText, "Query execution failed");
            alertWidget("error", `Query HTTP error (${resp.status}): ${detail}`);
          }

          results.push({
            frame_id: frameId,
            query,
            ok,
            query_status: status,
            status: resp.status,
            result: data,
            error_detail: ok ? "" : this.getEflintErrorDetail(resp, data, responseText, "Query execution failed"),
          });
        }

        this.queryExecutionStatusByFrame = statusByFrame;

        this.evaluationOutput = JSON.stringify(
          {
            session_id: sessionId,
            query_count: queryPairs.length,
            results,
          },
          null,
          2,
        );
      } catch (error) {
        this.evaluationOutput = error?.message || "Query execution failed";
      } finally {
        this.isRunningQueries = false;
      }
    },

    async evaluateQueries() {
      this.isEvaluatingQueries = true;
      this.queryExecutionStatusByFrame = {};
      this.evaluationOutput = "";

      try {
        const sessionId = await this.recreateEflintServerSession();

        const specification = await this.executeSpecification(sessionId);
        if (!this.isSuccessfulEflintResult(specification.resp, specification.data)) {
          const detail = this.getEflintErrorDetail(
            specification.resp,
            specification.data,
            specification.responseText,
            "Specification execution failed",
          );
          alertWidget("error", `Specification execution failed: ${detail}`);
          return;
        }

        const scenario = await this.executeScenario(sessionId);
        if (!this.isSuccessfulEflintResult(scenario.resp, scenario.data)) {
          const detail = this.getEflintErrorDetail(
            scenario.resp,
            scenario.data,
            scenario.responseText,
            "Scenario execution failed",
          );
          alertWidget("error", `Scenario execution failed: ${detail}`);
          return;
        }

        await this.runQueries();
      } catch (error) {
        alertWidget("error", error?.message || "Evaluation pipeline failed");
      } finally {
        this.isEvaluatingQueries = false;
      }
    },
  },
};
</script>
