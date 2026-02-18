<script>
  import { onMount } from 'svelte';
  import { Sun, Moon, Database, RefreshCw, Trash2, Users, ShieldCheck, ShieldAlert } from 'lucide-svelte';
    import { VERSION } from 'svelte/compiler';
  
  // CONFIGURATION
  const API_URL = '/api'; // Change if using NodePort/LoadBalancer
  const APP_VERSION = '1.1.0';
  
  // STATE
  let users = [];
  let isDarkMode = true;
  let isAutoRefreshing = false;
  let isLoading = false;
  let pollInterval;
  let error = null;

  // --- ACTIONS ---

async function fetchUsers() {
  try {
    // STEP 1: The network request SUCCEEDS (Status 200).
    const res = await fetch(`${API_URL}/users/?limit=100`);

    // STEP 2: This passes because res.ok is true.
    if (!res.ok) throw new Error("Failed to connect to API");

    // The browser refuses to let JavaScript read the JSON because of the missing CORS header.
    users = await res.json(); 
    error = null;

  } catch (e) {
    // STEP 4: The code jumps here immediately.
    error = "Backend Disconnected"; 
    console.error(e);
  }
}

  async function populateData() {
    isLoading = true;
    try {
      await fetch(`${API_URL}/populate_50`, { method: 'POST' });
      await fetchUsers();
    } catch (e) {
      alert("Failed to populate data");
    } finally {
      isLoading = false;
    }
  }
  
  async function deleteAllUsers() {
    if (!confirm("Are you sure you want to delete ALL users? This cannot be undone.")) return;

    isLoading = true;
    try {
      const res = await fetch(`${API_URL}/users/`, { method: 'DELETE' });
      if (!res.ok) throw new Error("Failed to delete");
      
      // Refresh the list (which should now be empty)
      await fetchUsers();
    } catch (e) {
      console.error(e);
      alert("Failed to delete users. Check backend connection.");
    } finally {
      isLoading = false;
    }
}

  // Toggle Auto-Refresh (The "Live" View)
  function toggleLiveMode() {
    isAutoRefreshing = !isAutoRefreshing;
    if (isAutoRefreshing) {
      pollInterval = setInterval(fetchUsers, 1000); // Poll every second
    } else {
      clearInterval(pollInterval);
    }
  }

  // Theme Toggler
  function toggleTheme() {
    isDarkMode = !isDarkMode;
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }

  // Helper to detect if data looks "Sanitized" (Simple heuristic for demo visuals)
  $: isSanitized = users.length > 0 && users.some(u => u.firstname.includes('*') || u.firstname.includes('Anonymized'));

  onMount(() => {
    document.documentElement.classList.add('dark'); // Default to dark
    fetchUsers();
  });
</script>

<nav class="sticky top-0 z-50 w-full border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md">
  <div class="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
    <div class="flex items-center gap-3">
        <img src="/IssTech_Symbol_white_landscape_200x50.png" alt="IssTech Logo" class="h-8 hidden dark:block" />
        <img src="/IssTech_Symbol_white_landscape_200x50.png" alt="IssTech Logo" class="h-8 block dark:hidden invert filter" /> 
        
        <div class="h-6 w-px bg-slate-300 dark:bg-slate-700 mx-2"></div>
        <span class="font-semibold text-slate-600 dark:text-slate-300 tracking-tight">K8s Backup Demo</span>
    </div>

    <div class="flex items-center gap-4">
      <button 
        on:click={toggleTheme}
        class="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
      >
        {#if isDarkMode} <Sun size={20} /> {:else} <Moon size={20} /> {/if}
      </button>
    </div>
  </div>
</nav>

<main class="max-w-7xl mx-auto px-4 py-8">
  
  <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
    
    <div class="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 relative overflow-hidden group">
      <div class="flex justify-between items-start">
        <div>
          <p class="text-sm font-medium text-slate-500 dark:text-slate-400">Total Records</p>
          <h3 class="text-3xl font-bold mt-2">{users.length}</h3>
        </div>
        <div class="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl text-blue-600 dark:text-blue-400">
          <Users size={24} />
        </div>
      </div>
    </div>

    <div class="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700">
      <div class="flex justify-between items-start">
        <div>
          <p class="text-sm font-medium text-slate-500 dark:text-slate-400">Data Integrity</p>
          <div class="flex items-center gap-2 mt-2">
            {#if isSanitized}
              <h3 class="text-3xl font-bold text-green-500">Sanitized</h3>
            {:else}
              <h3 class="text-3xl font-bold text-amber-500">Raw PII</h3>
            {/if}
          </div>
        </div>
        <div class={`p-3 rounded-xl ${isSanitized ? 'bg-green-50 text-green-600 dark:bg-green-900/20' : 'bg-amber-50 text-amber-600 dark:bg-amber-900/20'}`}>
          {#if isSanitized} <ShieldCheck size={24} /> {:else} <ShieldAlert size={24} /> {/if}
        </div>
      </div>
    </div>

    <div class="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700">
      <div class="flex justify-between items-start">
        <div>
          <p class="text-sm font-medium text-slate-500 dark:text-slate-400">Backend Status</p>
          <h3 class="text-3xl font-bold mt-2 flex items-center gap-2">
            {#if error}
              <span class="text-red-500 text-xl">Disconnected</span>
            {:else}
              <span class="text-isstech-500">Online</span>
              <span class="relative flex h-3 w-3">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
              </span>
            {/if}
          </h3>
        </div>
        <div class="p-3 bg-slate-100 dark:bg-slate-700 rounded-xl">
          <Database size={24} />
        </div>
      </div>
    </div>
  </div>

  <div class="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
    <div class="flex items-center gap-2">
      <h2 class="text-xl font-bold">User Database</h2>
      {#if isLoading}
        <RefreshCw class="animate-spin text-slate-400" size={18} />
      {/if}
    </div>

    <div class="flex items-center gap-3">
        <button 
            on:click={toggleLiveMode}
            class={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all border ${isAutoRefreshing ? 'bg-red-500/10 border-red-500/50 text-red-500' : 'bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-600'}`}
        >
            <div class={`w-2 h-2 rounded-full ${isAutoRefreshing ? 'bg-red-500 animate-pulse' : 'bg-slate-400'}`}></div>
            {isAutoRefreshing ? 'Live Monitoring ON' : 'Live Monitor OFF'}
        </button>

        <button 
            on:click={populateData}
            disabled={isLoading}
            class="flex items-center gap-2 px-4 py-2 bg-isstech-500 hover:bg-isstech-900 text-white rounded-lg font-medium shadow-lg shadow-isstech-500/30 transition-all active:scale-95 disabled:opacity-50"
        >
            <Database size={18} />
            Populate DB (50)
        </button>

        <button 
            on:click={deleteAllUsers}
            disabled={isLoading || users.length === 0}
            class="flex items-center gap-2 px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/50 rounded-lg font-medium transition-all active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed"
        >
            <Trash2 size={18} />
            Delete All
        </button>
    </div>
  </div>

  <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
    {#if users.length === 0 && !error}
        <div class="p-12 text-center text-slate-500">
            <Database size={48} class="mx-auto mb-4 opacity-20" />
            <p>Database is empty.</p>
            <p class="text-sm mt-1">Click "Populate DB" to start the demo.</p>
        </div>
    {:else if error}
        <div class="p-12 text-center text-red-500">
            <p class="font-bold">Connection Failed</p>
            <p class="text-sm mt-1">Ensure the FastAPI backend is running and CORS is enabled.</p>
        </div>
    {:else}
        <div class="overflow-x-auto">
            <table class="w-full text-left">
                <thead class="bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700">
                    <tr>
                        <th class="p-4 font-semibold text-slate-600 dark:text-slate-400">ID</th>
                        <th class="p-4 font-semibold text-slate-600 dark:text-slate-400">First Name</th>
                        <th class="p-4 font-semibold text-slate-600 dark:text-slate-400">Last Name</th>
                        <th class="p-4 font-semibold text-slate-600 dark:text-slate-400">Country</th>
                        <th class="p-4 font-semibold text-slate-600 dark:text-slate-400">Zip Code</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-100 dark:divide-slate-700/50">
                    {#each users as user (user.id)}
                        <tr class="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
                            <td class="p-4 font-mono text-xs text-slate-400">#{user.id}</td>
                            <td class="p-4 font-medium text-isstech-500 dark:text-green-400">{user.firstname}</td>
                            <td class="p-4">{user.lastname}</td>
                            <td class="p-4">
                                <span class="px-2 py-1 rounded text-xs bg-slate-100 dark:bg-slate-700 border border-slate-200 dark:border-slate-600">
                                    {user.country}
                                </span>
                            </td>
                            <td class="p-4 font-mono text-sm">{user.zip_code}</td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {/if}
  </div>
</main>

<footer class="py-6 text-center">
  <p class="text-xs text-slate-400 dark:text-slate-600 font-mono">
    IssTech Backup Demo • v{APP_VERSION}
  </p>
</footer>

<style>
    /* Custom scrollbar for table */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: transparent; 
    }
    ::-webkit-scrollbar-thumb {
        background: #94a3b8; 
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #64748b; 
    }
</style>