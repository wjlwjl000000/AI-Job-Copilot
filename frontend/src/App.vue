<template>
  <div class="layout">
    <aside class="sidebar">
      <h2>AI Job Copilot</h2>
      <nav>
        <router-link to="/">工作台</router-link>
        <router-link to="/chat">智能对话</router-link>
        <router-link to="/profile">求职画像</router-link>
        <router-link to="/resumes">简历管理</router-link>
        <router-link to="/jobs">职位匹配</router-link>
        <router-link to="/applications">投递追踪</router-link>
        <router-link to="/interview">面试备战</router-link>
        <router-link to="/support">情感支持</router-link>
        <router-link to="/agents">Agent 管理</router-link>
      </nav>
    </aside>
    <main class="content">
      <router-view v-slot="{ Component }">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </main>
  </div>
</template>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Microsoft YaHei', 'Segoe UI', sans-serif; background: #f5f5f5; }
.layout { display: flex; height: 100vh; }
.sidebar { width: 200px; background: #1a1a2e; color: white; padding: 20px; flex-shrink: 0; }
.sidebar h2 { font-size: 16px; margin-bottom: 24px; color: #e94560; }
.sidebar nav { display: flex; flex-direction: column; gap: 4px; }
.sidebar a { color: #a0a0b0; text-decoration: none; padding: 8px 12px; border-radius: 6px; font-size: 14px; transition: all 0.2s; }
.sidebar a:hover, .sidebar a.router-link-active { background: #16213e; color: white; }
.content { flex: 1; overflow-y: auto; padding: 32px; }
</style>
