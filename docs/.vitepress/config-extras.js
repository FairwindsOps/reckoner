// Project-owned. The shared VitePress config loads this file.
// Sidebar groups may use the VuePress shape (title, path, children, collapsable)
// or the VitePress shape (text, link, items, collapsed).
// Set themeConfig.docsBranch when the default branch is not master.
// https://vitepress.dev/reference/default-theme-sidebar
module.exports = {
  title: "Reckoner Documentation",
  description: "Documentation for Fairwinds' Reckoner",
  themeConfig: {
    docsRepo: "FairwindsOps/reckoner",
    sidebar: [
      {
        title: "Reckoner",
        path: "/",
      },
      {
        title: "Usage",
        path: "/usage",
      },
      {
        title: "Contributing",
        children: [
          {
            title: "Guide",
            path: "contributing/guide"
          },
          {
            title: "Code of Conduct",
            path: "contributing/code-of-conduct"
          }
        ]
      }
    ]
  },
}

