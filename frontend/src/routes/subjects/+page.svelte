<script lang="ts">
    import { onMount } from "svelte";

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
        score: number;
        matched_subject: string;
    }

    let subjects = $state<string[]>([]);
    let newSubject = $state("");
    let papers = $state<Paper[]>([]);
    let loading = $state(false);
    let searched = $state(false);
    let threshold = $state(60);

    const API_URL = "http://localhost:5000/api";

    onMount(() => {
        // Load saved subjects from localStorage
        const saved = localStorage.getItem("mySubjects");
        if (saved) {
            subjects = JSON.parse(saved);
        }
    });

    function saveSubjects() {
        localStorage.setItem("mySubjects", JSON.stringify(subjects));
    }

    function addSubject() {
        const trimmed = newSubject.trim();
        if (trimmed && !subjects.includes(trimmed)) {
            subjects = [...subjects, trimmed];
            saveSubjects();
            newSubject = "";
        }
    }

    function removeSubject(subject: string) {
        subjects = subjects.filter((s) => s !== subject);
        saveSubjects();
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === "Enter") {
            addSubject();
        }
    }

    async function findPapers() {
        if (subjects.length === 0) {
            alert("Please add at least one subject first");
            return;
        }

        loading = true;
        searched = true;

        try {
            const res = await fetch(`${API_URL}/papers/find-by-subjects`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    subjects: subjects,
                    threshold: threshold,
                    limit: 100,
                }),
            });

            if (res.ok) {
                const data = await res.json();
                if (data.success) {
                    papers = data.data;
                } else {
                    alert(data.error || "Failed to search");
                }
            } else {
                alert("Failed to connect to server");
            }
        } catch (e) {
            alert(
                "Failed to connect to server. Make sure the backend is running.",
            );
        }

        loading = false;
    }

    function downloadPaper(paper: Paper) {
        const url = paper.storage_url || paper.pdf_url;
        window.open(url, "_blank");
    }

    function getScoreColor(score: number): string {
        if (score >= 90) return "text-green-400";
        if (score >= 75) return "text-emerald-400";
        if (score >= 60) return "text-yellow-400";
        return "text-orange-400";
    }

    function getScoreBg(score: number): string {
        if (score >= 90) return "bg-green-500/10";
        if (score >= 75) return "bg-emerald-500/10";
        if (score >= 60) return "bg-yellow-500/10";
        return "bg-orange-500/10";
    }
</script>

<div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <!-- Header -->
    <div class="mb-8">
        <h1 class="text-3xl font-bold text-white mb-2">My Subjects</h1>
        <p class="text-slate-400">
            Add your subjects and find matching question papers instantly
        </p>
    </div>

    <!-- Add Subject Section -->
    <div class="glass-card p-6 mb-8">
        <h2 class="text-lg font-semibold text-white mb-4">Add Subjects</h2>

        <div class="flex gap-3 mb-6">
            <input
                type="text"
                bind:value={newSubject}
                onkeydown={handleKeydown}
                placeholder="Enter subject name (e.g., Data Structures, Machine Learning)"
                class="flex-1 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-primary-500/50 focus:ring-2 focus:ring-primary-500/20"
            />
            <button
                onclick={addSubject}
                class="px-6 py-3 bg-gradient-to-r from-primary-500 to-primary-600 text-white font-semibold rounded-xl hover:from-primary-600 hover:to-primary-700 transition-all"
            >
                Add
            </button>
        </div>

        <!-- Subject Tags -->
        {#if subjects.length > 0}
            <div class="flex flex-wrap gap-2 mb-4">
                {#each subjects as subject}
                    <div
                        class="flex items-center gap-2 px-4 py-2 bg-primary-500/10 border border-primary-500/20 rounded-xl"
                    >
                        <span class="text-primary-300">{subject}</span>
                        <button
                            onclick={() => removeSubject(subject)}
                            class="text-primary-400 hover:text-red-400 transition-colors"
                        >
                            <svg
                                class="w-4 h-4"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M6 18L18 6M6 6l12 12"
                                />
                            </svg>
                        </button>
                    </div>
                {/each}
            </div>
        {:else}
            <p class="text-slate-500 text-sm">
                No subjects added yet. Add subjects above to find matching
                papers.
            </p>
        {/if}
    </div>

    <!-- Search Options -->
    <div class="glass-card p-6 mb-8">
        <div
            class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
        >
            <div class="flex items-center gap-4">
                <label class="text-slate-300 text-sm">Match Sensitivity:</label>
                <select
                    bind:value={threshold}
                    class="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-primary-500/50"
                >
                    <option value={80}>High (80%+)</option>
                    <option value={60}>Medium (60%+)</option>
                    <option value={40}>Low (40%+)</option>
                </select>
            </div>

            <button
                onclick={findPapers}
                disabled={loading || subjects.length === 0}
                class="px-8 py-3 bg-gradient-to-r from-accent-500 to-accent-600 text-white font-semibold rounded-xl hover:from-accent-600 hover:to-accent-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
                {#if loading}
                    <svg
                        class="animate-spin h-5 w-5"
                        fill="none"
                        viewBox="0 0 24 24"
                    >
                        <circle
                            class="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            stroke-width="4"
                        ></circle>
                        <path
                            class="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        ></path>
                    </svg>
                    Searching...
                {:else}
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
                            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                        />
                    </svg>
                    Find Papers
                {/if}
            </button>
        </div>
    </div>

    <!-- Results -->
    {#if searched}
        <div class="mb-4">
            <h2 class="text-xl font-semibold text-white">
                {#if papers.length > 0}
                    Found {papers.length} Matching Papers
                {:else}
                    No Matching Papers Found
                {/if}
            </h2>
            <p class="text-slate-400 text-sm mt-1">
                Papers are sorted by match quality
            </p>
        </div>

        {#if papers.length > 0}
            <div class="space-y-4">
                {#each papers as paper}
                    <div class="glass-card p-5 paper-card">
                        <div class="flex items-start justify-between gap-4">
                            <div class="flex-1 min-w-0">
                                <div class="flex items-center gap-3 mb-2">
                                    <h3
                                        class="font-semibold text-white truncate"
                                        title={paper.title}
                                    >
                                        {paper.subject_name || paper.title}
                                    </h3>
                                    <span
                                        class={`px-2 py-1 rounded-md text-xs font-medium ${getScoreBg(paper.score)} ${getScoreColor(paper.score)}`}
                                    >
                                        {paper.score}% match
                                    </span>
                                </div>

                                {#if paper.subject_code}
                                    <p class="text-primary-400 text-sm mb-2">
                                        {paper.subject_code}
                                    </p>
                                {/if}

                                <p class="text-slate-500 text-sm">
                                    Matched: <span class="text-slate-400"
                                        >{paper.matched_subject}</span
                                    >
                                </p>
                            </div>

                            <button
                                onclick={() => downloadPaper(paper)}
                                class="p-3 bg-primary-500/10 text-primary-400 rounded-xl hover:bg-primary-500/20 transition-colors flex-shrink-0"
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
        {:else}
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
                            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                    </svg>
                </div>
                <h3 class="text-lg font-semibold text-white mb-2">
                    No Matches Found
                </h3>
                <p class="text-slate-400 mb-4">
                    Try adjusting the sensitivity or make sure papers have been
                    scraped first.
                </p>
                <a
                    href="/admin"
                    class="inline-flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                >
                    Go to Admin to Scrape Papers
                </a>
            </div>
        {/if}
    {/if}

    <!-- How it works -->
    {#if !searched}
        <div class="glass-card p-6">
            <h2 class="text-lg font-semibold text-white mb-4">How It Works</h2>
            <ul class="space-y-3 text-slate-400">
                <li class="flex items-start gap-3">
                    <span
                        class="w-6 h-6 bg-primary-500/20 text-primary-400 rounded-full flex items-center justify-center text-sm flex-shrink-0"
                        >1</span
                    >
                    <span
                        >Add subject names you're looking for (e.g., "Data
                        Structures", "Operating Systems")</span
                    >
                </li>
                <li class="flex items-start gap-3">
                    <span
                        class="w-6 h-6 bg-primary-500/20 text-primary-400 rounded-full flex items-center justify-center text-sm flex-shrink-0"
                        >2</span
                    >
                    <span
                        >Click "Find Papers" to search with smart fuzzy matching</span
                    >
                </li>
                <li class="flex items-start gap-3">
                    <span
                        class="w-6 h-6 bg-primary-500/20 text-primary-400 rounded-full flex items-center justify-center text-sm flex-shrink-0"
                        >3</span
                    >
                    <span
                        >Papers are ranked by match quality - even partial
                        matches are found!</span
                    >
                </li>
                <li class="flex items-start gap-3">
                    <span
                        class="w-6 h-6 bg-primary-500/20 text-primary-400 rounded-full flex items-center justify-center text-sm flex-shrink-0"
                        >4</span
                    >
                    <span
                        >Your subjects are saved locally, so they'll be here
                        next time</span
                    >
                </li>
            </ul>
        </div>
    {/if}
</div>
