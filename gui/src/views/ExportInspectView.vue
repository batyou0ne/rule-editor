<template>
  <div class="export-view q-pa-md">

    <!-- Header -->
    <div class="section-header q-mb-md">
      <div class="row items-center justify-between">
        <div>
          <div class="view-title">Project Inspector &amp; Export</div>
          <div class="view-subtitle">
            {{ taskLabel || 'No interpretation loaded' }}
          </div>
        </div>
        <div class="row q-gutter-sm">
          <q-btn
            icon="mdi-folder-download-outline"
            label="Export to folder"
            color="primary"
            unelevated
            :disable="!hasData"
            @click="exportToFolder"
          >
            <q-tooltip>Downloads a ZIP with metadata.json, flint/frames.json and eflint/specification.eflint</q-tooltip>
          </q-btn>
          <q-btn
            icon="mdi-github"
            label="Push to GitHub"
            color="dark"
            unelevated
            :disable="!hasData"
            @click="sections.github = true"
          >
            <q-tooltip>Push project files directly to a GitHub repository</q-tooltip>
          </q-btn>
        </div>
      </div>
    </div>

    <div v-if="!hasData" class="empty-state">
      <q-icon name="mdi-information-outline" size="48px" color="grey-5" />
      <div class="q-mt-sm text-grey-6">Load an interpretation first (Load button in the top bar).</div>
    </div>

    <template v-else>

      <!-- GITHUB PUSH PANEL -->
      <q-expansion-item
        v-model="sections.github"
        icon="mdi-github"
        label="Push to GitHub"
        header-class="section-title-github"
        class="inspection-card q-mb-md"
        expand-separator
      >
        <q-card flat>
          <q-card-section>

            <!-- Server-side token notice -->
            <q-banner dense rounded class="bg-blue-1 text-blue-9 q-mb-md">
              <template v-slot:avatar>
                <q-icon name="mdi-shield-key-outline" color="blue-7" />
              </template>
              Your GitHub token is stored on the server — you never need to enter it here.
            </q-banner>

            <div class="row q-gutter-md q-mb-md">
              <!-- Repo -->
              <div class="col-12 col-sm-8">
                <q-input
                  v-model="github.repo"
                  label="Repository (owner/name)"
                  outlined
                  dense
                  placeholder="e.g. my-org/flint-project"
                  hint="Will be created automatically if it doesn't exist yet."
                  @update:model-value="saveGithubSettings"
                >
                  <template v-slot:prepend>
                    <q-icon name="mdi-source-repository" />
                  </template>
                </q-input>
              </div>
            </div>

            <!-- Commit message -->
            <div class="row q-mb-md">
              <div class="col-12">
                <q-input
                  v-model="github.commitMessage"
                  label="Commit message"
                  outlined
                  dense
                >
                  <template v-slot:prepend>
                    <q-icon name="mdi-source-commit" />
                  </template>
                </q-input>
              </div>
            </div>

            <!-- Progress log -->
            <div v-if="github.log.length" class="github-log q-mb-md">
              <div
                v-for="(entry, i) in github.log"
                :key="i"
                :class="['log-line', `log-${entry.type}`]"
              >
                <q-icon :name="logIcon(entry.type)" size="14px" class="q-mr-xs" />
                {{ entry.message }}
              </div>
            </div>

            <!-- Action row -->
            <div class="row items-center q-gutter-sm">
              <q-btn
                icon="mdi-source-repository-multiple"
                :label="github.pushing ? 'Pushing…' : 'Push to GitHub'"
                color="dark"
                unelevated
                :loading="github.pushing"
                :disable="!github.repo"
                @click="pushToGithub"
              />
              <q-btn
                v-if="github.repoUrl"
                icon="mdi-open-in-new"
                label="Open repo"
                flat
                color="primary"
                :href="github.repoUrl"
                target="_blank"
              />
              <q-btn
                flat
                dense
                size="sm"
                icon="mdi-delete-outline"
                label="Clear saved settings"
                color="negative"
                @click="clearGithubSettings"
              />
            </div>

          </q-card-section>
        </q-card>
      </q-expansion-item>

      <!-- METADATA -->
      <q-expansion-item
        v-model="sections.metadata"
        icon="mdi-information-outline"
        label="Metadata"
        header-class="section-title"
        class="inspection-card q-mb-md"
        expand-separator
      >
        <q-card flat>
          <q-card-section>
            <div class="meta-grid">
              <div class="meta-row" v-for="row in metadataRows" :key="row.label">
                <span class="meta-label">{{ row.label }}</span>
                <span class="meta-value">{{ row.value }}</span>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </q-expansion-item>

      <!-- FLINT FRAMES -->
      <q-expansion-item
        v-model="sections.flint"
        icon="mdi-file-tree"
        :label="`FLINT Frames (${frames.length})`"
        header-class="section-title"
        class="inspection-card q-mb-md"
        expand-separator
      >
        <q-card flat>
          <q-card-section>
            <div class="row q-gutter-xs q-mb-md">
              <q-chip
                v-for="type in frameTypes"
                :key="type.id"
                :icon="type.icon"
                clickable
                :color="frameFilter === type.id ? 'primary' : 'grey-3'"
                :text-color="frameFilter === type.id ? 'white' : 'grey-8'"
                @click="frameFilter = frameFilter === type.id ? null : type.id"
              >
                {{ type.label }} ({{ frameCountByType(type.id) }})
              </q-chip>
              <q-chip
                v-if="frameFilter"
                icon="mdi-close"
                clickable
                color="grey-3"
                text-color="grey-8"
                @click="frameFilter = null"
              >
                Clear filter
              </q-chip>
            </div>

            <q-list separator>
              <q-expansion-item
                v-for="frame in filteredFrames"
                :key="frame.id"
                dense
                expand-separator
              >
                <template v-slot:header>
                  <q-item-section avatar>
                    <q-icon :name="iconForType(frame.typeId)" :color="colorForType(frame.typeId)" size="20px" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>{{ frame.shortName || frame.label || '(unnamed)' }}</q-item-label>
                    <q-item-label caption>{{ labelForType(frame.typeId) }}</q-item-label>
                  </q-item-section>
                  <q-item-section side>
                    <q-badge v-if="frame.subTypeIds?.length" color="blue-grey-2" text-color="blue-grey-8" :label="frame.subTypeIds.join(', ')" />
                  </q-item-section>
                </template>

                <q-card flat class="frame-detail-card">
                  <q-card-section>
                    <div class="meta-grid">
                      <div class="meta-row">
                        <span class="meta-label">ID</span>
                        <span class="meta-value code">{{ frame.id }}</span>
                      </div>
                      <div class="meta-row" v-if="frame.fullName || frame.fact">
                        <span class="meta-label">Full name</span>
                        <span class="meta-value">{{ frame.fullName || frame.fact }}</span>
                      </div>
                      <div class="meta-row" v-if="frame.typeId === 'act'">
                        <span class="meta-label">Actor</span>
                        <span class="meta-value">{{ resolveFrameName(frame.actorId) }}</span>
                      </div>
                      <div class="meta-row" v-if="frame.typeId === 'act'">
                        <span class="meta-label">Action</span>
                        <span class="meta-value">{{ resolveFrameName(frame.actionId) }}</span>
                      </div>
                      <div class="meta-row" v-if="frame.typeId === 'act'">
                        <span class="meta-label">Object</span>
                        <span class="meta-value">{{ resolveFrameName(frame.objectId) }}</span>
                      </div>
                      <div class="meta-row" v-if="frame.typeId === 'act' && frame.createsIds?.length">
                        <span class="meta-label">Creates</span>
                        <span class="meta-value">{{ frame.createsIds.map(resolveFrameName).join(', ') }}</span>
                      </div>
                      <div class="meta-row" v-if="frame.typeId === 'act' && frame.terminatesIds?.length">
                        <span class="meta-label">Terminates</span>
                        <span class="meta-value">{{ frame.terminatesIds.map(resolveFrameName).join(', ') }}</span>
                      </div>
                      <div class="meta-row" v-if="frame.typeId === 'claim_duty'">
                        <span class="meta-label">Duty</span>
                        <span class="meta-value">{{ resolveFrameName(frame.dutyId) }}</span>
                      </div>
                      <div class="meta-row" v-if="frame.typeId === 'claim_duty'">
                        <span class="meta-label">Claimant</span>
                        <span class="meta-value">{{ resolveFrameName(frame.claimantId) }}</span>
                      </div>
                      <div class="meta-row" v-if="frame.typeId === 'claim_duty'">
                        <span class="meta-label">Holder</span>
                        <span class="meta-value">{{ resolveFrameName(frame.holderId) }}</span>
                      </div>
                      <div class="meta-row" v-if="frame.comments?.length">
                        <span class="meta-label">Comments</span>
                        <span class="meta-value">{{ frame.comments.length }} comment(s)</span>
                      </div>
                    </div>
                  </q-card-section>
                </q-card>
              </q-expansion-item>
            </q-list>
          </q-card-section>
        </q-card>
      </q-expansion-item>

      <!-- eFLINT -->
      <q-expansion-item
        v-model="sections.eflint"
        icon="mdi-code-braces"
        label="eFLINT Specification"
        header-class="section-title"
        class="inspection-card q-mb-md"
        expand-separator
      >
        <q-card flat>
          <q-card-section>
            <div v-if="eflintCode" class="row items-center justify-between q-mb-sm">
              <span class="text-caption text-grey-6">{{ eflintLineCount }} lines</span>
              <q-btn flat dense size="sm" icon="mdi-content-copy" label="Copy" @click="copyEflint" />
            </div>
            <div v-if="eflintCode" class="eflint-code-block">
              <pre>{{ eflintCode }}</pre>
            </div>
            <div v-else class="text-grey-6 text-body2">
              No eFLINT code generated yet. Use the "Make interpretations executable" tab first.
            </div>
          </q-card-section>
        </q-card>
      </q-expansion-item>

    </template>
  </div>
</template>

<script>
import JSZip from 'jszip'
import { saveAs } from 'file-saver'
import { useQuasar } from 'quasar'

const STORAGE_KEY = 'flint-editor.github'

export default {
  name: 'ExportInspectView',

  setup() {
    const $q = useQuasar()
    return { $q }
  },

  data() {
    const saved = (() => {
      try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') } catch { return {} }
    })()
    return {
      sections: {
        github: false,
        metadata: true,
        flint: true,
        eflint: true,
      },
      frameFilter: null,
      frameTypes: [
        { id: 'fact',       label: 'Fact',       icon: 'mdi-card-text-outline' },
        { id: 'act',        label: 'Act',         icon: 'mdi-lightning-bolt' },
        { id: 'claim_duty', label: 'Claim-Duty',  icon: 'mdi-handshake' },
      ],
      github: {
        repo:          saved.repo   || '',
        commitMessage: `FLINT export: ${new Date().toISOString().slice(0, 10)}`,
        pushing:       false,
        repoUrl:       saved.repoUrl || '',
        log:           [],
      },
    }
  },

  computed: {
    task()       { return this.$store.state.task },
    frames()     { return this.$store.state.frames },
    eflintCode() { return this.$store.state.executableEflintBase || this.$store.state.executableEflintFinal || '' },
    hasData()    { return this.task && (this.frames.length > 0 || this.eflintCode) },
    taskLabel()  { return this.task?.label || '' },

    metadataRows() {
      if (!this.task) return []
      return [
        { label: 'Title',        value: this.task.label || '—' },
        { label: 'Description',  value: this.task.description || '—' },
        { label: 'Editor',       value: this.task.editor || this.task.editorName || '—' },
        { label: 'Task IRI',     value: this.task.id || this.task.iri || '—' },
        { label: 'Total frames', value: this.frames.length },
        { label: 'Facts',        value: this.frames.filter(f => f.typeId === 'fact').length },
        { label: 'Acts',         value: this.frames.filter(f => f.typeId === 'act').length },
        { label: 'Claim-Duties', value: this.frames.filter(f => f.typeId === 'claim_duty').length },
      ].filter(r => r.value !== '—' || r.label === 'Description')
    },

    filteredFrames() {
      const list = this.frames.map(f => f.toFlatObject ? f.toFlatObject() : f)
      return this.frameFilter ? list.filter(f => f.typeId === this.frameFilter) : list
    },

    eflintLineCount() {
      return this.eflintCode ? this.eflintCode.split('\n').length : 0
    },
  },

  methods: {
    // ─── helpers ───────────────────────────────────────────────
    frameCountByType(typeId)  { return this.frames.filter(f => f.typeId === typeId).length },
    iconForType(typeId)       { return { fact: 'mdi-card-text-outline', act: 'mdi-lightning-bolt', claim_duty: 'mdi-handshake' }[typeId] || 'mdi-help' },
    colorForType(typeId)      { return { fact: 'primary', act: 'secondary', claim_duty: 'accent' }[typeId] || 'grey' },
    labelForType(typeId)      { return { fact: 'Fact', act: 'Act', claim_duty: 'Claim-Duty' }[typeId] || typeId },
    logIcon(type)             { return { info: 'mdi-information-outline', ok: 'mdi-check-circle-outline', error: 'mdi-alert-circle-outline', warn: 'mdi-alert-outline' }[type] || 'mdi-circle-small' },

    resolveFrameName(id) {
      if (!id) return '—'
      const frame = this.frames.find(f => f.id === id)
      return frame ? (frame.shortName || frame.label || id) : id
    },

    copyEflint() {
      navigator.clipboard.writeText(this.eflintCode)
      this.$q.notify({ type: 'positive', message: 'Copied to clipboard', timeout: 1500 })
    },

    saveGithubSettings() {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        repo:    this.github.repo,
        repoUrl: this.github.repoUrl,
      }))
    },

    clearGithubSettings() {
      this.github.repo    = ''
      this.github.repoUrl = ''
      localStorage.removeItem(STORAGE_KEY)
      this.$q.notify({ type: 'info', message: 'GitHub settings cleared', timeout: 1500 })
    },

    // ─── build file map ────────────────────────────────────────
    buildFileMap() {
      const meta = {
        title:       this.task?.label || '',
        description: this.task?.description || '',
        editor:      this.task?.editor || this.task?.editorName || '',
        task_iri:    this.task?.id || this.task?.iri || '',
        exported_at: new Date().toISOString(),
      }
      const framesFlat = this.frames.map(f => f.toFlatObject ? f.toFlatObject() : f)
      const slug = (this.task?.label || 'flint-project').replace(/[^a-z0-9]/gi, '_').toLowerCase()
      const readme = [
        `# ${this.task?.label || 'FLINT Project'}`,
        '',
        `> Exported from FLINT Rule Editor on ${new Date().toLocaleDateString()}`,
        '',
        '## Structure',
        '- `metadata.json` — task metadata',
        '- `flint/frames.json` — FLINT frames (facts, acts, claim-duties)',
        '- `eflint/specification.eflint` — generated eFLINT code',
      ].join('\n')

      const files = {
        'README.md':          readme,
        'metadata.json':      JSON.stringify(meta, null, 2),
        'flint/frames.json':  JSON.stringify(framesFlat, null, 2),
      }
      if (this.eflintCode) {
        files['eflint/specification.eflint'] = this.eflintCode
      }
      return { files, slug }
    },

    // ─── github push (via server-side git-service) ────────────
    async pushToGithub() {
      const { repo, commitMessage } = this.github
      if (!repo) return

      this.github.pushing = true
      this.github.log = []

      const log = (message, type = 'info') => this.github.log.push({ message, type })

      try {
        log(`Sending ${repo} to git-service…`)
        const { files, slug } = this.buildFileMap()

        const prefixed = {}
        for (const [path, content] of Object.entries(files)) {
          prefixed[`${slug}/${path}`] = content
        }

        const res = await fetch('/git-service/push', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ repo, files: prefixed, commit_message: commitMessage }),
        })

        const data = await res.json()
        if (!res.ok) {
          throw new Error(data.detail || `Server error ${res.status}`)
        }

        this.github.repoUrl = data.repo_url
        this.saveGithubSettings()

        log(`Version: ${data.version}`, 'info')
        for (const f of data.pushed) {
          log(`✓ ${f.path} (${f.status})`, 'ok')
        }
        log('All files pushed successfully!', 'ok')

        this.$q.notify({
          type: 'positive',
          icon: 'mdi-github',
          message: 'Pushed to GitHub',
          caption: data.repo_url,
          timeout: 6000,
          actions: [{ label: 'Open', color: 'white', handler: () => window.open(data.repo_url, '_blank') }],
        })

      } catch (err) {
        log(err.message, 'error')
        this.$q.notify({ type: 'negative', message: err.message, timeout: 5000 })
      } finally {
        this.github.pushing = false
      }
    },

    // ─── zip download ──────────────────────────────────────────
    async exportToFolder() {
      const zip = new JSZip()
      const { files, slug } = this.buildFileMap()
      const now = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)

      for (const [path, content] of Object.entries(files)) {
        const parts = path.split('/')
        if (parts.length === 2) {
          zip.folder(parts[0]).file(parts[1], content)
        } else {
          zip.file(path, content)
        }
      }

      const blob = await zip.generateAsync({ type: 'blob' })
      saveAs(blob, `${slug}_${now}.zip`)

      this.$q.notify({
        type: 'positive',
        icon: 'mdi-folder-download-outline',
        message: `Exported as ${slug}_${now}.zip`,
        caption: 'Unzip, then run git init inside the folder.',
        timeout: 5000,
      })
    },
  },
}
</script>

<style scoped>
.export-view {
  max-width: 900px;
  margin: 0 auto;
}

.view-title {
  font-size: 18px;
  font-weight: 700;
  color: #1B2A4A;
  font-family: 'Inter', sans-serif;
}

.view-subtitle {
  font-size: 13px;
  color: #5A6A80;
  margin-top: 2px;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
}

.inspection-card {
  border: 1px solid #E2E6EC;
  border-radius: 8px;
  overflow: hidden;
}

.section-title {
  font-weight: 600;
  color: #1B2A4A;
  background: #F8F9FB;
}

.section-title-github {
  font-weight: 600;
  color: #ffffff;
  background: #1B2A4A;
}

.meta-grid {
  display: grid;
  gap: 8px;
}

.meta-row {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: 12px;
  align-items: start;
  padding: 6px 0;
  border-bottom: 1px solid #F0F2F5;
}

.meta-row:last-child {
  border-bottom: none;
}

.meta-label {
  font-size: 12px;
  font-weight: 600;
  color: #5A6A80;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding-top: 1px;
}

.meta-value {
  font-size: 13px;
  color: #1B2A4A;
  word-break: break-all;
}

.meta-value.code {
  font-family: monospace;
  font-size: 11px;
  color: #3A7CA5;
}

.frame-detail-card {
  background: #F8F9FB;
  margin: 4px 16px 8px;
  border: 1px solid #E2E6EC;
  border-radius: 6px;
}

.eflint-code-block {
  background: #0D1B2A;
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
}

.eflint-code-block pre {
  margin: 0;
  font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: #C8D4E8;
  white-space: pre-wrap;
  word-break: break-word;
}

/* GitHub push log */
.github-log {
  background: #0D1B2A;
  border-radius: 8px;
  padding: 12px 14px;
  display: grid;
  gap: 4px;
}

.log-line {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 12px;
  display: flex;
  align-items: center;
}

.log-info  { color: #7A9AB8; }
.log-ok    { color: #6FCF97; }
.log-error { color: #EB5757; }
.log-warn  { color: #F0C96A; }
</style>
