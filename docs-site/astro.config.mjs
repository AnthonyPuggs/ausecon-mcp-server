import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://auseconmcp.com',
  integrations: [
    starlight({
      title: 'AusEcon MCP Server',
      description: 'Documentation for Australian economic data from the ABS and RBA over MCP.',
      editLink: {
        baseUrl: 'https://github.com/AnthonyPuggs/ausecon-mcp-server/edit/main/docs-site/',
      },
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
          items: [{ label: 'Caching and Logging', slug: 'operations/caching-and-logging' }],
        },
        {
          label: 'Maintainers',
          items: [
            { label: 'Contributing', slug: 'maintainers/contributing' },
            { label: 'Releasing', slug: 'maintainers/releasing' },
          ],
        },
      ],
    }),
  ],
});
