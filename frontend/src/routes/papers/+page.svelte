<script lang="ts">
    import { onMount } from "svelte";
    import { page } from "$app/stores";

    interface Paper {
        id: string;
        title: string;
        subject_code: string;
        subject_name: string;
        year: string;
        semester: string;
        branch: string;
        exam_type: string;
        pdf_url: string;
        storage_url: string;
    }

    interface Filters {
        years: string[];
        semesters: string[];
        branches: string[];
    }

    let papers = $state<Paper[]>([]);
    let filters = $state<Filters>({ years: [], semesters: [], branches: [] });
    let loading = $state(true);
    let error = $state("");

    // Filter state
    let selectedYear = $state("");
    let selectedSemester = $state("");
    let selectedBranch = $state("");
    let searchQuery = $state("");

    const API_URL = "http://localhost:5000/api";

    onMount(async () => {
        // Get URL params
        const params = new URLSearchParams(window.location.search);
        selectedYear = params.get("year") || "";
        selectedBranch = params.get("branch") || "";
        searchQuery = params.get("search") || "";

        await Promise.all([loadFilters(), loadPapers()]);
    });

    async function loadFilters() {
        try {
            const res = await fetch(`${API_URL}/filters`);
            if (res.ok) {
                const data = await res.json();
                if (data.success) {
                    filters = data.data;
                }
            }
        } catch (e) {
            console.error("Failed to load filters:", e);
        }
    }

    async function loadPapers() {
        loading = true;
        error = "";

        try {
            const params = new URLSearchParams();
            if (selectedYear) params.set("year", selectedYear);
            if (selectedSemester) params.set("semester", selectedSemester);
            if (selectedBranch) params.set("branch", selectedBranch);
            if (searchQuery) params.set("search", searchQuery);
            params.set("limit", "50");

            const res = await fetch(`${API_URL}/papers?${params}`);
            if (res.ok) {
                const data = await res.json();
                if (data.success) {
                    papers = data.data;
                } else {
                    error = data.error || "Failed to load papers";
                }
            } else {
                error =
                    "Failed to connect to server. Make sure the backend is running.";
            }
        } catch (e) {
            error =
                "Failed to connect to server. Make sure the backend is running on port 5000.";
        }

        loading = false;
    }

    function handleSearch() {
        loadPapers();
    }

    function clearFilters() {
        selectedYear = "";
        selectedSemester = "";
        selectedBranch = "";
        searchQuery = "";
        loadPapers();
    }

    async function downloadPaper(paper: Paper) {
        const url = paper.storage_url || paper.pdf_url;
        window.open(url, "_blank");
    }
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <!-- Header -->
    <div class="mb-8">
        <h1 class="text-3xl font-bold text-white mb-2">Question Papers</h1>
        <p class="text-slate-400">
            Browse and download previous year question papers
        </p>
    </div>

    <div class="flex flex-col lg:flex-row gap-8">
        <!-- Filters Sidebar -->
        <aside class="lg:w-72 flex-shrink-0">
            <div class="glass-card p-6 sticky top-24">
                <h2 class="text-lg font-semibold text-white mb-4">Filters</h2>

                <!-- Search -->
                <div class="mb-6">
                    <label class="block text-sm font-medium text-slate-300 mb-2"
                        >Search</label
                    >
                    <input
                        type="text"
                        bind:value={searchQuery}
                        on:keydown={(e) => e.key === "Enter" && handleSearch()}
                        placeholder="Subject name or code..."
                        class="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-primary-500/50"
                    />
                </div>

                <!-- Year Filter -->
                <div class="mb-4">
                    <label class="block text-sm font-medium text-slate-300 mb-2"
                        >Year</label
                    >
                    <select
                        bind:value={selectedYear}
                        on:change={handleSearch}
                        class="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-primary-500/50"
                    >
                        <option value="">All Years</option>
                        {#each filters.years as year}
                            <option value={year}>{year}</option>
                        {/each}
                    </select>
                </div>

                <!-- Semester Filter -->
                <div class="mb-4">
                    <label class="block text-sm font-medium text-slate-300 mb-2"
                        >Semester</label
                    >
                    <select
                        bind:value={selectedSemester}
                        on:change={handleSearch}
                        class="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-primary-500/50"
                    >
                        <option value="">All Semesters</option>
                        {#each filters.semesters as sem}
                            <option value={sem}>{sem}</option>
                        {/each}
                    </select>
                </div>

                <!-- Branch Filter -->
                <div class="mb-6">
                    <label class="block text-sm font-medium text-slate-300 mb-2"
                        >Branch</label
                    >
                    <select
                        bind:value={selectedBranch}
                        on:change={handleSearch}
                        class="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-primary-500/50"
                    >
                        <option value="">All Branches</option>
                        {#each filters.branches as branch}
                            <option value={branch}>{branch}</option>
                        {/each}
                    </select>
                </div>

                <!-- Action Buttons -->
                <div class="flex gap-2">
                    <button
                        on:click={handleSearch}
                        class="flex-1 px-4 py-2 bg-primary-500 text-white font-medium rounded-lg hover:bg-primary-600 transition-colors"
                    >
                        Apply
                    </button>
                    <button
                        on:click={clearFilters}
                        class="px-4 py-2 bg-white/5 text-slate-300 font-medium rounded-lg hover:bg-white/10 transition-colors"
                    >
                        Clear
                    </button>
                </div>
            </div>
        </aside>

        <!-- Papers Grid -->
        <main class="flex-1">
            {#if loading}
                <div class="flex items-center justify-center py-20">
                    <div
                        class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"
                    ></div>
                </div>
            {:else if error}
                <div class="glass-card p-8 text-center">
                    <div
                        class="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-4"
                    >
                        <svg
                            class="w-8 h-8 text-red-400"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                        </svg>
                    </div>
                    <h3 class="text-lg font-semibold text-white mb-2">
                        Connection Error
                    </h3>
                    <p class="text-slate-400 mb-4">{error}</p>
                    <button
                        on:click={loadPapers}
                        class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                    >
                        Try Again
                    </button>
                </div>
            {:else if papers.length === 0}
                <div class="glass-card p-8 text-center">
                    <div
                        class="w-16 h-16 bg-slate-500/10 rounded-full flex items-center justify-center mx-auto mb-4"
                    >
                        <svg
                            class="w-8 h-8 text-slate-400"
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
                    <h3 class="text-lg font-semibold text-white mb-2">
                        No Papers Found
                    </h3>
                    <p class="text-slate-400">
                        No papers match your current filters. Try adjusting your
                        search criteria or run a scrape from the Admin panel.
                    </p>
                </div>
            {:else}
                <div class="mb-4 text-slate-400">
                    Found {papers.length} paper{papers.length === 1 ? "" : "s"}
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {#each papers as paper}
                        <div class="glass-card p-5 paper-card">
                            <div class="flex items-start justify-between gap-4">
                                <div class="flex-1 min-w-0">
                                    <h3
                                        class="font-semibold text-white truncate"
                                        title={paper.title}
                                    >
                                        {paper.subject_name || paper.title}
                                    </h3>
                                    {#if paper.subject_code}
                                        <p class="text-primary-400 text-sm">
                                            {paper.subject_code}
                                        </p>
                                    {/if}
                                </div>
                                <button
                                    on:click={() => downloadPaper(paper)}
                                    class="p-2 bg-primary-500/10 text-primary-400 rounded-lg hover:bg-primary-500/20 transition-colors flex-shrink-0"
                                    title="Download PDF"
                                >
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
                                            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                                        />
                                    </svg>
                                </button>
                            </div>

                            <div class="mt-3 flex flex-wrap gap-2">
                                {#if paper.year}
                                    <span
                                        class="px-2 py-1 bg-blue-500/10 text-blue-400 text-xs rounded-md"
                                        >{paper.year}</span
                                    >
                                {/if}
                                {#if paper.semester}
                                    <span
                                        class="px-2 py-1 bg-purple-500/10 text-purple-400 text-xs rounded-md"
                                        >{paper.semester}</span
                                    >
                                {/if}
                                {#if paper.branch}
                                    <span
                                        class="px-2 py-1 bg-green-500/10 text-green-400 text-xs rounded-md"
                                        >{paper.branch}</span
                                    >
                                {/if}
                                {#if paper.exam_type && paper.exam_type !== "Regular"}
                                    <span
                                        class="px-2 py-1 bg-orange-500/10 text-orange-400 text-xs rounded-md"
                                        >{paper.exam_type}</span
                                    >
                                {/if}
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
        </main>
    </div>
</div>
