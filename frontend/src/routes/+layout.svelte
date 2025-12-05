<script lang="ts">
  import "../app.css";
  let { children } = $props();
</script>

<svelte:head>
  <title>PYQ Finder - MIT Manipal Question Papers</title>
  <meta
    name="description"
    content="Search and download previous year question papers from MIT Manipal library"
  />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
</svelte:head>

<div
  class="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950"
>
  <!-- Background decoration -->
  <div class="fixed inset-0 overflow-hidden pointer-events-none">
    <div
      class="absolute -top-40 -right-40 w-80 h-80 bg-primary-500/20 rounded-full blur-3xl"
    ></div>
    <div
      class="absolute -bottom-40 -left-40 w-80 h-80 bg-accent-500/20 rounded-full blur-3xl"
    ></div>
    <div
      class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-primary-600/10 rounded-full blur-3xl"
    ></div>
  </div>

  <!-- Navigation -->
  <nav
    class="relative z-50 border-b border-white/10 backdrop-blur-xl bg-slate-900/50"
  >
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <a href="/" class="flex items-center gap-3">
          <div
            class="p-2 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl"
          >
            <svg
              class="w-6 h-6 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <span class="text-xl font-bold gradient-text">PYQ Finder</span>
        </a>

        <div class="flex items-center gap-6">
          <a
            href="/"
            class="text-slate-300 hover:text-white transition-colors font-medium"
            >Home</a
          >
          <a
            href="/subjects"
            class="text-slate-300 hover:text-white transition-colors font-medium"
            >My Subjects</a
          >
          <a
            href="/papers"
            class="text-slate-300 hover:text-white transition-colors font-medium"
            >Papers</a
          >
          <a
            href="/admin"
            class="text-slate-300 hover:text-white transition-colors font-medium"
            >Admin</a
          >
        </div>
      </div>
    </div>
  </nav>

  <!-- Main content -->
  <main class="relative z-10">
    {@render children()}
  </main>

  <!-- Footer -->
  <footer class="relative z-10 border-t border-white/10 mt-20">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="flex flex-col md:flex-row items-center justify-between gap-4">
        <p class="text-slate-400 text-sm">
          © 2024 PYQ Finder. Made for MIT Manipal students.
        </p>
        <div class="flex items-center gap-4">
          <a
            href="https://github.com"
            target="_blank"
            class="text-slate-400 hover:text-white transition-colors"
          >
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path
                d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"
              />
            </svg>
          </a>
        </div>
      </div>
    </div>
  </footer>
</div>
