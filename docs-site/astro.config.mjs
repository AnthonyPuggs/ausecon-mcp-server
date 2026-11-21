import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://auseconmcp.com',
  vite: {
    cacheDir: process.env.VITE_CACHE_DIR || 'node_modules/.vite',
  },
  integrations: [
    starlight({
      title: 'ausecon MCP Server',
      description:
        'Documentation for ausecon, an independent MCP server for Australian economic data from the ABS, RBA and APRA.',
      components: {
        // Adds the independence disclaimer under every page.
        Footer: './src/components/Footer.astro',
      },
      // Brand colours (from the banner and logo) and the home page layout.
      customCss: ['./src/styles/custom.css'],
      logo: {
        src: './src/assets/logo.png',
        alt: 'ausecon logo',
      },
      favicon: '/favicon.svg',
      editLink: {
        baseUrl: 'https://github.com/AnthonyPuggs/ausecon-mcp-server/edit/main/docs-site/',
      },
      head: [
        // Fallback icons for browsers without SVG favicon support, and the iOS home-screen icon.
        { tag: 'link', attrs: { rel: 'icon', href: '/favicon.ico', sizes: '32x32' } },
        { tag: 'link', attrs: { rel: 'apple-touch-icon', href: '/apple-touch-icon.png' } },
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
            { label: 'Inline Charts', slug: 'user-guide/inline-charts' },
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
            { label: 'Privacy Policy', slug: 'privacy' },
            { label: 'Data Sources and Licensing', slug: 'data-sources' },
          ],
        },
        {
          label: 'Maintainers',
          items: [
            { label: 'Contributing', slug: 'maintainers/contributing' },
            { label: 'Evaluation Harness', slug: 'maintainers/evaluation' },
            { label: 'Releasing', slug: 'maintainers/releasing' },
            { label: 'Roadmap', slug: 'maintainers/roadmap' },
          ],
        },
      ],
    }),
  ],
});
