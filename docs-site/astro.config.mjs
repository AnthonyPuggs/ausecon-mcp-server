import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://auseconmcp.com',
  vite: {
    cacheDir: process.env.VITE_CACHE_DIR || 'node_modules/.vite',
  },
  integrations: [
    starlight({
      title: 'AusEcon MCP Server',
      description: 'Documentation for Australian economic data from the ABS and RBA over MCP.',
      logo: {
        src: './src/assets/logo.png',
        alt: 'ausecon logo',
      },
      editLink: {
        baseUrl: 'https://github.com/AnthonyPuggs/ausecon-mcp-server/edit/main/docs-site/',
      },
      head: [
        // Vercel Web Analytics + Speed Insights. Starlight owns the page layout,
        // so the plain script tags are injected here rather than via the
        // @vercel/analytics Astro components (which only work in a custom layout).
        {
          tag: 'script',
          content:
            'window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };' +
            'window.speedInsightsBeforeSend = function (payload) {' +
            ' try { if (payload && payload.url) { var u = new URL(payload.url); u.search = ""; u.hash = ""; payload.url = u.toString(); } } catch (e) {}' +
            ' return payload; };',
        },
        { tag: 'script', attrs: { defer: true, src: '/_vercel/insights/script.js' } },
        { tag: 'script', attrs: { defer: true, src: '/_vercel/speed-insights/script.js' } },
      ],
      social: [
        {
          icon: 'github',
          label: 'GitHub',
          href: 'https://github.com/AnthonyPuggs/ausecon-mcp-server',
        },
      ],
      sidebar: [
        {
          label: 'Start',
          items: [
            { label: 'Overview', slug: 'index' },
            { label: 'Getting Started', slug: 'getting-started' },
            { label: 'Client Setup', slug: 'client-setup' },
          ],
        },
        {
          label: 'User Guide',
          items: [
            { label: 'Discovery and Retrieval', slug: 'user-guide/discovery-and-retrieval' },
            { label: 'Prompting AI Agents', slug: 'user-guide/prompting-ai-agents' },
            { label: 'Data Freshness and Provenance', slug: 'user-guide/data-freshness-and-provenance' },
            { label: 'Examples', slug: 'user-guide/examples' },
          ],
        },
        {
          label: 'Reference',
          items: [
            { label: 'Tools', slug: 'reference/tools' },
            { label: 'Resources and Prompts', slug: 'reference/resources-and-prompts' },
            { label: 'Semantic Concepts', slug: 'reference/semantic-concepts' },
            { label: 'Response Schema', slug: 'reference/response-schema' },
            { label: 'Semantic Variants', slug: 'reference/semantic-variants' },
          ],
        },
        {
          label: 'Operations',
          items: [
            { label: 'Caching and Logging', slug: 'operations/caching-and-logging' },
            { label: 'Hosted Deployment', slug: 'operations/hosted-deployment' },
          ],
        },
        {
          label: 'Maintainers',
          items: [
            { label: 'Contributing', slug: 'maintainers/contributing' },
            { label: 'Releasing', slug: 'maintainers/releasing' },
            { label: 'Roadmap', slug: 'maintainers/roadmap' },
          ],
        },
      ],
    }),
  ],
});
