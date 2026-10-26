// Tells Astro what a blog post looks like. Every file in src/content/writing
// must have these fields at the top, or the build stops and says which is wrong.
import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const writing = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/writing' }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    tag: z.enum(['Devotional', 'Reflection', 'Building']),
    summary: z.string(),
    draft: z.boolean().default(false),
  }),
});

export const collections = { writing };
