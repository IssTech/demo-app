<script>
  import { onMount } from 'svelte';
  import { Sun, Moon, Database, RefreshCw, Trash2, Users, ShieldCheck, ShieldAlert, Sparkles, MessageSquare, Send, X, Bot, Loader2 } from 'lucide-svelte';
    import { VERSION } from 'svelte/compiler';
  
  // CONFIGURATION
  const API_URL = '/api'; // Change if using NodePort/LoadBalancer
  const APP_VERSION = '1.1.0';
  
  // STATE
  let users = [];
  let totalUsers = 0;
  let currentPage = 1;
  let pageSize = 25;
  let isDarkMode = true;
  let isAutoRefreshing = false;
  let isLoading = false;
  let pollInterval;
  let error = null;

  $: totalPages = Math.ceil(totalUsers / pageSize) || 1;

  // --- ACTIONS ---

  async function fetchUsers() {
    try {
      const skip = (currentPage - 1) * pageSize;
      const res = await fetch(`${API_URL}/users/?skip=${skip}&limit=${pageSize}`);
      if (!res.ok) throw new Error("Failed to connect to API");

      users = await res.json();
      
      // Retrieve the total user count from the custom header (fallback to local length if missing)
      const totalHeader = res.headers.get('X-Total-Count');
      totalUsers = totalHeader ? parseInt(totalHeader, 10) : users.length;
      
      error = null;
    } catch (e) {
      error = "Backend Disconnected"; 
      console.error(e);
    }
  }

  function handlePageSizeChange(e) {
    pageSize = parseInt(e.target.value, 10);
    currentPage = 1;
    fetchUsers();
  }

  function changePage(page) {
    if (page >= 1 && page <= totalPages) {
      currentPage = page;
      fetchUsers();
    }
  }

  async function populateData() {
    isLoading = true;
    try {
      await fetch(`${API_URL}/populate_50`, { method: 'POST' });
      currentPage = 1;
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
      
      currentPage = 1;
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

  // --- AGENTIC AI CHAT STATE & FUNCTIONS ---
  let isChatOpen = false;
  let chatInput = "";
  let chatMessages = [
    { role: "assistant", content: "Hello! I am your Agentic AI assistant, powered by a local Ollama LLM. I can query and analyze any data inside our PostgreSQL database in real-time. Ask me a question, such as:\n• 'How many users are in the database?'\n• 'Where are the users from?'\n• 'List all users from Sweden or Norway'\n• 'Show me a breakdown of users by country'" }
  ];
  let isSending = false;
  let chatContainer;

  function scrollToBottom() {
    if (chatContainer) {
      setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }, 50);
    }
  }

  async function sendChatMessage() {
    if (!chatInput.trim() || isSending) return;

    const userText = chatInput.trim();
    chatInput = "";
    
    // Append user message
    chatMessages = [...chatMessages, { role: "user", content: userText }];
    scrollToBottom();
    isSending = true;

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          messages: chatMessages.map(m => ({ role: m.role, content: m.content }))
        })
      });

      if (!res.ok) {
        throw new Error("Chat request failed");
      }

      const reply = await res.json();
      chatMessages = [...chatMessages, { role: "assistant", content: reply.response }];
    } catch (e) {
      console.error(e);
      chatMessages = [...chatMessages, { 
        role: "assistant", 
        content: "Sorry, I had trouble connecting to the local Ollama model. Please verify that the backend and Ollama are running." 
      }];
    } finally {
      isSending = false;
      scrollToBottom();
    }
  }

  function handleKeydown(e) {
    if (e.key === "Enter") {
      sendChatMessage();
    }
  }

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
          <h3 class="text-3xl font-bold mt-2">{totalUsers}</h3>
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

        <!-- Pagination Controls -->
        <div class="border-t border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/30 px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-500 dark:text-slate-400">
            <div class="flex items-center gap-4">
                <div class="flex items-center gap-2">
                    <span>Show</span>
                    <select 
                        value={pageSize} 
                        on:change={handlePageSizeChange}
                        class="bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg px-2.5 py-1 text-slate-700 dark:text-white focus:outline-none focus:ring-1 focus:ring-isstech-500 focus:border-isstech-500 text-sm"
                    >
                        <option value={25}>25</option>
                        <option value={50}>50</option>
                        <option value={100}>100</option>
                    </select>
                    <span>records</span>
                </div>
                <div class="h-4 w-px bg-slate-200 dark:bg-slate-700 hidden sm:block"></div>
                <div>
                    Showing <span class="font-semibold text-slate-700 dark:text-slate-300">{users.length > 0 ? (currentPage - 1) * pageSize + 1 : 0}</span> to 
                    <span class="font-semibold text-slate-700 dark:text-slate-300">{Math.min(currentPage * pageSize, totalUsers)}</span> of 
                    <span class="font-semibold text-slate-700 dark:text-slate-300">{totalUsers}</span> records
                </div>
            </div>

            <div class="flex items-center gap-1.5">
                <button 
                    on:click={() => changePage(currentPage - 1)}
                    disabled={currentPage === 1}
                    class="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-xs"
                >
                    Previous
                </button>

                {#each Array(totalPages) as _, i}
                    <button 
                        on:click={() => changePage(i + 1)}
                        class={`px-3 py-1.5 rounded-lg border font-medium text-xs transition-all ${
                            currentPage === i + 1 
                                ? 'bg-isstech-500 text-white border-isstech-500 shadow-md shadow-isstech-500/20' 
                                : 'border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'
                        }`}
                    >
                        {i + 1}
                    </button>
                {/each}

                <button 
                    on:click={() => changePage(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    class="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-xs"
                >
                    Next
                </button>
            </div>
        </div>
    {/if}
  </div>
</main>

<footer class="py-6 text-center">
  <p class="text-xs text-slate-400 dark:text-slate-600 font-mono">
    IssTech Backup Demo • v{APP_VERSION}
  </p>
</footer>

<!-- Floating Agentic AI Chat Widget -->
<div class="fixed bottom-6 right-6 z-50 flex flex-col items-end">
  {#if isChatOpen}
    <div 
      class="w-96 max-w-[calc(100vw-2rem)] h-[500px] max-h-[calc(100vh-8rem)] bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 flex flex-col overflow-hidden mb-4 transition-all duration-300"
    >
      <!-- Header -->
      <div class="p-4 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 text-white flex items-center justify-between border-b border-slate-200 dark:border-slate-800">
        <div class="flex items-center gap-2.5">
          <div class="p-1.5 bg-[#49E97F]/10 rounded-lg text-[#49E97F]">
            <Sparkles size={18} class="animate-pulse" />
          </div>
          <div class="text-left">
            <h4 class="font-bold text-sm tracking-tight text-white flex items-center gap-1.5">
              Agentic AI Assistant
            </h4>
            <div class="flex items-center gap-1.5 text-[11px] text-[#49E97F] font-mono mt-0.5">
              <span class="relative flex h-2 w-2">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
              Offline LLM Active
            </div>
          </div>
        </div>
        <button 
          on:click={() => isChatOpen = false}
          class="p-1 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-all"
        >
          <X size={18} />
        </button>
      </div>

      <!-- Chat Messages Container -->
      <div 
        bind:this={chatContainer}
        class="flex-1 p-4 overflow-y-auto space-y-3 bg-slate-50 dark:bg-slate-900/40 text-left"
      >
        {#each chatMessages as msg}
          <div class={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div class={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${
              msg.role === 'user' 
                ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-br-sm shadow-sm' 
                : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700 rounded-bl-sm shadow-sm'
            }`}>
              {#if msg.role === 'assistant'}
                <div class="flex items-start gap-2">
                  <div class="p-1 bg-[#49E97F]/10 rounded text-[#49E97F] mt-0.5 flex-shrink-0">
                    <Bot size={14} />
                  </div>
                  <div class="leading-relaxed whitespace-pre-wrap">{msg.content}</div>
                </div>
              {:else}
                <div class="leading-relaxed whitespace-pre-wrap">{msg.content}</div>
              {/if}
            </div>
          </div>
        {/each}

        {#if isSending}
          <div class="flex justify-start">
            <div class="max-w-[85%] bg-white dark:bg-slate-800 text-slate-500 rounded-2xl rounded-bl-sm px-4 py-3 text-sm border border-slate-200 dark:border-slate-700 shadow-sm flex items-center gap-2">
              <Loader2 size={16} class="animate-spin text-[#49E97F]" />
              <span class="animate-pulse">Agent is querying database...</span>
            </div>
          </div>
        {/if}
      </div>

      <!-- Input Form -->
      <div class="p-3 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 flex gap-2">
        <input 
          type="text"
          bind:value={chatInput}
          on:keydown={handleKeydown}
          placeholder="Ask database (e.g. Total users?)"
          class="flex-1 px-3.5 py-2 text-sm bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#49E97F]/40 focus:border-[#49E97F] dark:text-white"
        />
        <button 
          on:click={sendChatMessage}
          disabled={!chatInput.trim() || isSending}
          class="p-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:opacity-40 text-white rounded-xl shadow-md transition-all flex items-center justify-center"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  {/if}

  <!-- Floating Toggle Button -->
  {#if !isChatOpen}
    <button 
      on:click={() => { isChatOpen = true; scrollToBottom(); }}
      class="p-4 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 hover:scale-105 active:scale-95 text-white rounded-full shadow-2xl transition-all flex items-center justify-center border-2 border-[#49E97F]"
      aria-label="Open Agentic AI"
    >
      <div class="relative">
        <Sparkles size={24} class="text-[#49E97F] animate-pulse" />
        <span class="absolute -top-1.5 -right-1.5 flex h-2.5 w-2.5">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
        </span>
      </div>
    </button>
  {/if}
</div>

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