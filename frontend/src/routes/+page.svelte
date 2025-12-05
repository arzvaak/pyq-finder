<script lang="ts">
    import { onMount } from "svelte";

    let searchQuery = $state("");
    let stats = $state({ papers: 0, subjects: 0, years: 0 });
    let loading = $state(true);

    onMount(async () => {
        try {
            const res = await fetch("http://localhost:5000/api/filters");
            if (res.ok) {
                const data = await res.json();
                if (data.success) {
                    stats = {
                        papers: 0, // Would need a count endpoint
                        subjects: data.data.branches?.length || 0,
                        years: data.data.years?.length || 0,
                    };
                }
            }
        } catch (e) {
            console.log("Backend not running yet");
        }
        loading = false;
    });

    function handleSearch() {
        if (searchQuery.trim()) {
            window.location.href = `/papers?search=${encodeURIComponent(searchQuery)}`;
        }
    }
</script>

<div class="py-12">
    <!-- Hero Section -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div class="text-center">
            <div
                class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-500/10 border border-primary-500/20 mb-6"
            >
                <span class="w-2 h-2 bg-green-400 rounded-full animate-pulse"
                ></span>
                <span class="text-primary-400 text-sm font-medium"
                    >MIT Manipal Library</span
                >
            </div>

            <h1 class="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6">
                <span class="text-white">Find Your</span>
                <br />
                <span class="gradient-text">Question Papers</span>
            </h1>

            <p
                class="text-slate-400 text-lg sm:text-xl max-w-2xl mx-auto mb-10"
            >
                Access previous year question papers from MIT Manipal library.
                Search by subject, year, semester, or branch.
            </p>

            <!-- Search Box -->
            <form
                on:submit|preventDefault={handleSearch}
                class="max-w-2xl mx-auto mb-12"
            >
                <div class="relative">
                    <input
                        type="text"
                        bind:value={searchQuery}
                        placeholder="Search for subjects, papers..."
                        class="w-full px-6 py-4 pl-14 bg-white/5 border border-white/10 rounded-2xl text-white placeholder-slate-400 focus:outline-none focus:border-primary-500/50 focus:ring-2 focus:ring-primary-500/20 transition-all"
                    />
                    <svg
                        class="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                        />
                    </svg>
                    <button
                        type="submit"
                        class="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-2 bg-gradient-to-r from-primary-500 to-primary-600 text-white font-medium rounded-xl hover:from-primary-600 hover:to-primary-700 transition-all"
                    >
                        Search
                    </button>
                </div>
            </form>

            <!-- Quick Links -->
            <div class="flex flex-wrap justify-center gap-3 mb-16">
                <a
                    href="/papers"
                    class="px-4 py-2 glass rounded-xl text-slate-300 hover:text-white hover:bg-white/10 transition-all"
                >
                    All Papers
                </a>
                <a
                    href="/papers?year=2024"
                    class="px-4 py-2 glass rounded-xl text-slate-300 hover:text-white hover:bg-white/10 transition-all"
                >
                    2024 Papers
                </a>
                <a
                    href="/papers?branch=Computer"
                    class="px-4 py-2 glass rounded-xl text-slate-300 hover:text-white hover:bg-white/10 transition-all"
                >
                    Computer Science
                </a>
                <a
                    href="/papers?branch=Electronics"
                    class="px-4 py-2 glass rounded-xl text-slate-300 hover:text-white hover:bg-white/10 transition-all"
                >
                    Electronics
                </a>
                <a
                    href="/papers?branch=Mechanical"
                    class="px-4 py-2 glass rounded-xl text-slate-300 hover:text-white hover:bg-white/10 transition-all"
                >
                    Mechanical
                </a>
            </div>
        </div>

        <!-- Stats -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <div class="glass-card p-6 text-center">
                <div class="text-4xl font-bold gradient-text mb-2">
                    {loading ? "..." : "1000+"}
                </div>
                <div class="text-slate-400">Question Papers</div>
            </div>
            <div class="glass-card p-6 text-center">
                <div class="text-4xl font-bold gradient-text mb-2">
                    {loading ? "..." : stats.subjects || "15+"}
                </div>
                <div class="text-slate-400">Branches</div>
            </div>
            <div class="glass-card p-6 text-center">
                <div class="text-4xl font-bold gradient-text mb-2">
                    {loading ? "..." : stats.years || "10+"}
                </div>
                <div class="text-slate-400">Years of Papers</div>
            </div>
        </div>
    </section>

    <!-- Features Section -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <h2 class="text-3xl font-bold text-white text-center mb-12">
            Why Use PYQ Finder?
        </h2>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div class="glass-card p-8">
                <div
                    class="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center mb-4"
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
                            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                        />
                    </svg>
                </div>
                <h3 class="text-xl font-semibold text-white mb-2">
                    Easy Search
                </h3>
                <p class="text-slate-400">
                    Find papers quickly by searching for subject name, code, or
                    year.
                </p>
            </div>

            <div class="glass-card p-8">
                <div
                    class="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center mb-4"
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
                            d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                        />
                    </svg>
                </div>
                <h3 class="text-xl font-semibold text-white mb-2">
                    Smart Filters
                </h3>
                <p class="text-slate-400">
                    Filter by year, semester, branch, and exam type to find
                    exactly what you need.
                </p>
            </div>

            <div class="glass-card p-8">
                <div
                    class="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center mb-4"
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
                            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                        />
                    </svg>
                </div>
                <h3 class="text-xl font-semibold text-white mb-2">
                    Fast Downloads
                </h3>
                <p class="text-slate-400">
                    Download papers directly as PDFs with a single click.
                </p>
            </div>
        </div>
    </section>

    <!-- CTA Section -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div class="glass-card p-12 text-center relative overflow-hidden">
            <div
                class="absolute inset-0 bg-gradient-to-r from-primary-500/10 to-accent-500/10"
            ></div>
            <div class="relative z-10">
                <h2 class="text-3xl font-bold text-white mb-4">
                    Ready to Find Your Papers?
                </h2>
                <p class="text-slate-400 mb-8 max-w-xl mx-auto">
                    Browse our collection of previous year question papers from
                    both MIT Manipal library portals.
                </p>
                <a
                    href="/papers"
                    class="inline-flex items-center gap-2 px-8 py-3 bg-gradient-to-r from-primary-500 to-primary-600 text-white font-semibold rounded-xl hover:from-primary-600 hover:to-primary-700 transition-all shadow-lg shadow-primary-500/25"
                >
                    Browse Papers
                    <svg
                        class="w-5 h-5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M13 7l5 5m0 0l-5 5m5-5H6"
                        />
                    </svg>
                </a>
            </div>
        </div>
    </section>
</div>
