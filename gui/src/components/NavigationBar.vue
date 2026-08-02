<template>
  <div class="nav-wrapper">
    <div class="nav-header">
      <div class="nav-brand">
        <q-icon name="mdi-scale-balance" size="24px" color="white" class="q-mr-sm" />
        <span class="nav-title">FLINT Rule Editor</span>
      </div>
      <div class="nav-actions">
        <q-btn
          flat dense size="sm" icon="mdi-history"
          text-color="white"
          @click="whatsNewOpen = true"
        >
          <q-tooltip>What's new?</q-tooltip>
        </q-btn>
        <LoadSaveInterpretationBanner/>
      </div>
      <WhatsNewModal v-model="whatsNewOpen" />
    </div>
    <div class="nav-tabs">
      <div class="nav-tabs-row">
        <div class="row items-center q-gutter-xs cursor-pointer nav-button"
          :class="{'selected': activeView?.id == view.id}"
          v-for="view in views"
          @click="this.updateActiveView(view)">
          <q-icon :name="view.icon" size="18px"/>
          <div>{{ view.label }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import TaskDefinitionView from "../views/TaskDefinitionView.vue";
import SourceCollectionView from "../views/SourceCollectionView.vue";
import InterpretationView from "../views/interpretation/InterpretationView.vue";
import VisualizationView from "../views/visualization/VisualizationView.vue";
import MakeExecutableView from "../views/executable/MakeExecutableView.vue";
import ExecuteTaskView from "../views/executable/ExecuteTaskView.vue";
import LoadSaveInterpretationBanner from "./LoadSaveIntepretationBanner.vue"
import WhatsNewModal from "./WhatsNewModal.vue"
import { markRaw } from 'vue'

export default {
    data: () => ({
    whatsNewOpen: false,
    views: [
      {
        id:0,
        label: "Set task",
        component: markRaw(TaskDefinitionView),
        completed: false,
        icon: 'mdi-head-dots-horizontal-outline'
      },
      {
        id: 1,
        label: "Collect sources",
        component: markRaw(SourceCollectionView),
        completed: false,
        icon: 'mdi-bookmark-box-multiple-outline'
      },
      {
        id: 2,
        label: "Interpret sources",
        component: markRaw(InterpretationView),
        completed: false,
        icon: 'mdi-thought-bubble-outline'
      },
      {
        id: 3,
        label: "View interpretation",
        component: markRaw(VisualizationView),
        completed: false,
        icon: 'mdi-file-tree'
      },
      {
        id: 4,
        label: "Make interpretations executable",
        component: markRaw(MakeExecutableView),
        completed: false,
        icon: 'mdi-timeline-check-outline'
      },
      {
        id: 5,
        label: "interactive eFLINT",
        component: markRaw(ExecuteTaskView),
        completed: false,
        icon: 'mdi-playlist-check'
      },
    ],
  }),
  props: {
    activeView: Object
  },
  components: {
    TaskDefinitionView,
    InterpretationView,
    SourceCollectionView,
    LoadSaveInterpretationBanner,
    WhatsNewModal,
  },
  mounted() {
    this.updateActiveView(this.views[0])
  },
  methods: {
    updateActiveView(newView) {
      this.$emit('update:activeView', newView);
    }
  }
}
</script>

<style>
.nav-wrapper {
  background: #fff;
  border-bottom: 1px solid #E2E6EC;
}
.nav-header {
  background: linear-gradient(135deg, #1B2A4A 0%, #243B5E 100%);
  padding: 10px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.nav-brand {
  display: flex;
  align-items: center;
}
.nav-title {
  font-family: 'Inter', sans-serif;
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0.02em;
}
.nav-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.nav-tabs {
  padding: 0 12px;
  background: #fff;
  overflow-x: auto;
  white-space: nowrap;
}
.nav-tabs-row {
  display: inline-flex;
  align-items: center;
  min-width: 100%;
  justify-content: center;
}
.nav-button {
  border-bottom: 2px solid transparent;
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 500;
  color: #5A6A80;
  transition: all 0.15s ease;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.nav-button:hover {
  color: #1B2A4A;
  border-bottom: 2px solid #C7963E;
  background: rgba(199, 150, 62, 0.04);
}
.nav-button.selected {
  color: #1B2A4A;
  border-bottom: 2px solid #C7963E;
  font-weight: 600;
}
</style>
