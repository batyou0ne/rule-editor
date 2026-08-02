<template>
  <q-dialog v-model="open" max-width="600px">
    <q-card style="width: 600px; max-width: 95vw; max-height: 80vh; display: flex; flex-direction: column;">
      <q-card-section class="changelog-header">
        <div class="row items-center no-wrap">
          <q-icon name="mdi-history" size="24px" color="white" class="q-mr-sm" />
          <div>
            <div class="changelog-title">FLINT Rule Editor — Changelog</div>
            <div class="changelog-subtitle">Complete history of features, fixes and improvements</div>
          </div>
        </div>
        <q-btn flat round dense icon="mdi-close" color="white" v-close-popup class="close-btn" />
      </q-card-section>

      <q-card-section class="scroll" style="flex: 1; overflow-y: auto; padding: 16px;">
        <div
          v-for="entry in changelog"
          :key="entry.version"
          class="version-block"
          :class="{ unreleased: entry.status === 'unreleased' }"
        >
          <div class="version-row" @click="toggleVersion(entry.version)">
            <div class="version-left">
              <span class="version-number">{{ entry.version }}</span>
              <span class="version-date">{{ entry.date }}</span>
            </div>
            <div class="version-right">
              <q-badge
                :color="entry.status === 'unreleased' ? 'orange' : 'positive'"
                :label="entry.status === 'unreleased' ? 'Unreleased' : 'Released'"
                class="q-mr-sm"
              />
              <q-icon :name="expanded.includes(entry.version) ? 'mdi-chevron-up' : 'mdi-chevron-down'" />
            </div>
          </div>

          <div v-if="expanded.includes(entry.version)" class="version-content">
            <div v-for="section in entry.sections" :key="section.type" class="section-block">
              <div class="section-title">
                <span v-if="section.type === 'Features'">✨</span>
                <span v-else-if="section.type === 'Fixes'">🔧</span>
                <span v-else>🧹</span>
                {{ section.type }}
              </div>
              <ul class="section-items">
                <li v-for="item in section.items" :key="item">{{ item }}</li>
              </ul>
            </div>
          </div>
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script>
import changelog from "../data/changelog.json";

export default {
  name: "WhatsNewModal",

  props: {
    modelValue: Boolean,
  },

  emits: ["update:modelValue"],

  data() {
    return {
      changelog,
      expanded: [changelog[0]?.version],
    };
  },

  computed: {
    open: {
      get() { return this.modelValue; },
      set(v) { this.$emit("update:modelValue", v); },
    },
  },

  methods: {
    toggleVersion(version) {
      const i = this.expanded.indexOf(version);
      if (i === -1) this.expanded.push(version);
      else this.expanded.splice(i, 1);
    },
  },
};
</script>

<style scoped>
.changelog-header {
  background: linear-gradient(135deg, #1B2A4A 0%, #243B5E 100%);
  color: white;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
}

.changelog-title {
  font-size: 16px;
  font-weight: 700;
  color: white;
}

.changelog-subtitle {
  font-size: 12px;
  color: rgba(255,255,255,0.7);
  margin-top: 2px;
}

.close-btn {
  position: absolute;
  right: 12px;
  top: 12px;
}

.version-block {
  border: 1px solid #E2E6EC;
  border-radius: 8px;
  margin-bottom: 10px;
  overflow: hidden;
}

.version-block.unreleased {
  border-color: #F5A623;
}

.version-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  background: #f9fafb;
  user-select: none;
}

.version-row:hover {
  background: #f0f3f7;
}

.version-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.version-number {
  font-weight: 700;
  font-size: 15px;
  color: #1B2A4A;
}

.version-date {
  font-size: 12px;
  color: #8A9BB0;
}

.version-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.version-content {
  padding: 12px 16px 16px;
  border-top: 1px solid #E2E6EC;
}

.section-block {
  margin-bottom: 12px;
}

.section-title {
  font-weight: 600;
  font-size: 13px;
  color: #1B2A4A;
  margin-bottom: 6px;
}

.section-items {
  margin: 0;
  padding-left: 20px;
}

.section-items li {
  font-size: 13px;
  color: #4A5568;
  margin-bottom: 4px;
  line-height: 1.5;
}
</style>
