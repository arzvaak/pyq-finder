<script lang="ts">
    import { onMount, onDestroy } from "svelte";

    interface ScrapeStatus {
        is_running: boolean;
        portal: string | null;
        progress: number;
        total: number;
        errors: string[];
        message: string;
    }

    let scrapeStatus = $state<ScrapeStatus>({
        is_running: false,
        portal: null,
        progress: 0,
        total: 0,
        errors: [],
        message: "",
    });

    let selectedPortal = $state("portal1");
    let selectedYears = $state<string[]>([]);
    let uploadToStorage = $state(true);
    let statusInterval: number | null = null;

    const API_URL = "http://localhost:5000/api";

    onMount(() => {
        checkStatus();
        statusInterval = setInterval(checkStatus, 2000) as unknown as number;
    });

    onDestroy(() => {
        if (statusInterval) clearInterval(statusInterval);
    });

    async function checkStatus() {
        try {
            const res = await fetch(`${API_URL}/scrape/status`);
            if (res.ok) {
                const data = await res.json();
                if (data.success) {
                    scrapeStatus = data.data;
                }
            }
        } catch (e) {
            // Backend not running
        }
    }

    async function startScrape() {
        try {
            const res = await fetch(`${API_URL}/scrape`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    portal: selectedPortal,
                    years: selectedYears.length > 0 ? selectedYears : null,
                    upload_to_storage: uploadToStorage,
                }),
            });

            if (res.ok) {
                const data = await res.json();
                if (data.success) {
                    scrapeStatus = {
                        ...scrapeStatus,
                        is_running: true,
                        message: "Starting...",
                    };
                } else {
                    alert(data.error || "Failed to start scrape");
                }
            }
        } catch (e) {
            alert(
                "Failed to connect to server. Make sure the backend is running.",
            );
        }
    }

    async function stopScrape() {
        try {
            const res = await fetch(`${API_URL}/scrape/stop`, {
                method: "POST",
            });
            if (res.ok) {
                checkStatus();
            }
        } catch (e) {
            alert("Failed to stop scrape");
        }
    }

    const availableYears = ["2020", "2021", "2022", "2023", "2024", "2025"];
</script>

<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="mb-8">
        <h1 class="text-3xl font-bold text-white mb-2">Admin Panel</h1>
        <p class="text-slate-400">
            Manage scraping jobs and update the paper database
        </p>
    </div>

    <!-- Status Card -->
    <div class="glass-card p-6 mb-8">
        <h2 class="text-lg font-semibold text-white mb-4">Scrape Status</h2>

        <div class="flex items-center gap-4 mb-4">
            <div class="flex items-center gap-2">
                <span
                    class={`w-3 h-3 rounded-full ${scrapeStatus.is_running ? "bg-green-400 animate-pulse" : "bg-slate-500"}`}
                ></span>
                <span class="text-white font-medium">
                    {scrapeStatus.is_running ? "Running" : "Idle"}
                </span>
            </div>

            {#if scrapeStatus.portal}
                <span
                    class="px-3 py-1 bg-primary-500/10 text-primary-400 text-sm rounded-lg"
                >
                    {scrapeStatus.portal}
                </span>
            {/if}
        </div>

        {#if scrapeStatus.message}
            <div class="p-4 bg-white/5 rounded-lg mb-4">
                <p class="text-slate-300 text-sm font-mono">
                    {scrapeStatus.message}
                </p>
            </div>
        {/if}

        {#if scrapeStatus.progress > 0}
            <div class="mb-4">
                <div class="flex justify-between text-sm text-slate-400 mb-1">
                    <span>Progress</span>
                    <span>{scrapeStatus.progress} papers scraped</span>
                </div>
                <div class="h-2 bg-white/5 rounded-full overflow-hidden">
                    <div
                        class="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full transition-all duration-300"
                        style="width: {Math.min(100, scrapeStatus.progress)}%"
                    ></div>
                </div>
            </div>
        {/if}

        {#if scrapeStatus.errors.length > 0}
            <div class="p-4 bg-red-500/10 rounded-lg">
                <h3 class="text-red-400 font-medium mb-2">
                    Errors ({scrapeStatus.errors.length})
                </h3>
                <ul
                    class="text-sm text-red-300 space-y-1 max-h-32 overflow-y-auto"
                >
                    {#each scrapeStatus.errors.slice(-5) as error}
                        <li class="truncate">{error}</li>
                    {/each}
                </ul>
            </div>
        {/if}
    </div>

    <!-- Start Scrape Card -->
    <div class="glass-card p-6">
        <h2 class="text-lg font-semibold text-white mb-4">Start New Scrape</h2>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <!-- Portal Selection -->
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-2"
                    >Select Portal</label
                >
                <div class="space-y-2">
                    <label
                        class="flex items-center gap-3 p-3 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors"
                    >
                        <input
                            type="radio"
                            bind:group={selectedPortal}
                            value="portal1"
                            class="text-primary-500"
                        />
                        <div>
                            <div class="text-white font-medium">Portal 1</div>
                            <div class="text-slate-400 text-sm">
                                mitmpllibportal.manipal.edu
                            </div>
                        </div>
                    </label>
                    <label
                        class="flex items-center gap-3 p-3 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors"
                    >
                        <input
                            type="radio"
                            bind:group={selectedPortal}
                            value="portal2"
                            class="text-primary-500"
                        />
                        <div>
                            <div class="text-white font-medium">
                                Portal 2 (Selenium)
                            </div>
                            <div class="text-slate-400 text-sm">
                                libportal.manipal.edu
                            </div>
                        </div>
                    </label>
                    <label
                        class="flex items-center gap-3 p-3 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors"
                    >
                        <input
                            type="radio"
                            bind:group={selectedPortal}
                            value="both"
                            class="text-primary-500"
                        />
                        <div>
                            <div class="text-white font-medium">
                                Both Portals
                            </div>
                            <div class="text-slate-400 text-sm">
                                Scrape from both sequentially
                            </div>
                        </div>
                    </label>
                </div>
            </div>

            <!-- Options -->
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-2"
                    >Options</label
                >

                <label
                    class="flex items-center gap-3 p-3 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors mb-3"
                >
                    <input
                        type="checkbox"
                        bind:checked={uploadToStorage}
                        class="rounded text-primary-500"
                    />
                    <div>
                        <div class="text-white font-medium">
                            Upload to Firebase Storage
                        </div>
                        <div class="text-slate-400 text-sm">
                            Store PDFs for faster downloads
                        </div>
                    </div>
                </label>

                {#if selectedPortal === "portal2" || selectedPortal === "both"}
                    <div>
                        <label class="block text-sm text-slate-400 mb-2"
                            >Years to scrape (optional)</label
                        >
                        <div class="flex flex-wrap gap-2">
                            {#each availableYears as year}
                                <label
                                    class="flex items-center gap-2 px-3 py-1 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors"
                                >
                                    <input
                                        type="checkbox"
                                        value={year}
                                        checked={selectedYears.includes(year)}
                                        on:change={(e) => {
                                            if (e.currentTarget.checked) {
                                                selectedYears = [
                                                    ...selectedYears,
                                                    year,
                                                ];
                                            } else {
                                                selectedYears =
                                                    selectedYears.filter(
                                                        (y) => y !== year,
                                                    );
                                            }
                                        }}
                                        class="rounded text-primary-500"
                                    />
                                    <span class="text-white text-sm"
                                        >{year}</span
                                    >
                                </label>
                            {/each}
                        </div>
                    </div>
                {/if}
            </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-4">
            {#if scrapeStatus.is_running}
                <button
                    on:click={stopScrape}
                    class="px-6 py-3 bg-red-500 text-white font-semibold rounded-xl hover:bg-red-600 transition-colors"
                >
                    Stop Scrape
                </button>
            {:else}
                <button
                    on:click={startScrape}
                    class="px-6 py-3 bg-gradient-to-r from-primary-500 to-primary-600 text-white font-semibold rounded-xl hover:from-primary-600 hover:to-primary-700 transition-all"
                >
                    Start Scrape
                </button>
            {/if}

            <a
                href="/papers"
                class="px-6 py-3 bg-white/5 text-slate-300 font-medium rounded-xl hover:bg-white/10 transition-colors"
            >
                View Papers
            </a>
        </div>
    </div>

    <!-- Info Card -->
    <div class="glass-card p-6 mt-8">
        <h2 class="text-lg font-semibold text-white mb-4">How It Works</h2>
        <ul class="space-y-3 text-slate-400">
            <li class="flex items-start gap-3">
                <span
                    class="w-6 h-6 bg-primary-500/20 text-primary-400 rounded-full flex items-center justify-center text-sm flex-shrink-0"
                    >1</span
                >
                <span>Select a portal to scrape papers from</span>
            </li>
            <li class="flex items-start gap-3">
                <span
                    class="w-6 h-6 bg-primary-500/20 text-primary-400 rounded-full flex items-center justify-center text-sm flex-shrink-0"
                    >2</span
                >
                <span
                    >The scraper will navigate the portal and find all PDF links</span
                >
            </li>
            <li class="flex items-start gap-3">
                <span
                    class="w-6 h-6 bg-primary-500/20 text-primary-400 rounded-full flex items-center justify-center text-sm flex-shrink-0"
                    >3</span
                >
                <span>Paper metadata is extracted and stored in Firebase</span>
            </li>
            <li class="flex items-start gap-3">
                <span
                    class="w-6 h-6 bg-primary-500/20 text-primary-400 rounded-full flex items-center justify-center text-sm flex-shrink-0"
                    >4</span
                >
                <span
                    >PDFs are uploaded to Firebase Storage for fast downloads</span
                >
            </li>
        </ul>
    </div>
</div>
