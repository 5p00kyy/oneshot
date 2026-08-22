// @ts-check
import { defineConfig } from "astro/config";

// The site is published under the repository subpath on GitHub Pages.
// `base` applies to both production builds and `npm run dev`
// (the dev server serves everything under /oneshot/).
export default defineConfig({
  site: "https://5p00kyy.github.io",
  base: "/oneshot/",
  output: "static",
  build: {
    inlineStylesheets: "always",
  },
});
