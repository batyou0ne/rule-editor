<template>
  <div class="login-page fit row items-center justify-center q-pa-md">
    <q-card flat bordered class="login-card" style="width: 100%; max-width: 420px;">
      <q-card-section class="login-header text-center">
        <q-icon name="mdi-scale-balance" size="36px" color="white" />
        <div class="login-title">FLINT Rule Editor</div>
        <div class="login-org">University of Amsterdam</div>
      </q-card-section>

      <q-card-section class="q-gutter-md q-pt-lg">
        <q-input
          v-model="username"
          label="Username"
          outlined
          dense
          autocomplete="username"
          @keyup.enter="submit"
        />
        <q-input
          v-model="password"
          label="Password"
          type="password"
          outlined
          dense
          autocomplete="current-password"
          @keyup.enter="submit"
        />
        <q-banner v-if="errorMessage" dense rounded class="bg-red-1 text-negative">
          {{ errorMessage }}
        </q-banner>
      </q-card-section>

      <q-card-actions class="q-px-md q-pb-md">
        <q-btn
          color="primary"
          label="Sign in"
          :loading="loading"
          @click="submit"
          class="full-width"
          unelevated
          size="md"
        />
      </q-card-actions>
    </q-card>
  </div>
</template>

<style scoped>
.login-page {
  background: linear-gradient(160deg, #1B2A4A 0%, #243B5E 40%, #3A7CA5 100%);
  min-height: 100vh;
}

.login-card {
  background: #fff !important;
  overflow: hidden;
}

.login-header {
  background: linear-gradient(135deg, #1B2A4A 0%, #243B5E 100%);
  padding: 28px 20px 24px !important;
}

.login-title {
  font-family: 'Inter', sans-serif;
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  margin-top: 10px;
}

.login-org {
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 4px;
}
</style>

<script>
export default {
  name: "LoginForm",
  props: {
    loading: {
      type: Boolean,
      default: false,
    },
    errorMessage: {
      type: String,
      default: "",
    },
  },
  emits: ["login"],
  data: () => ({
    username: "",
    password: "",
  }),
  methods: {
    submit() {
      this.$emit("login", {
        username: this.username,
        password: this.password,
      });
    },
  },
};
</script>