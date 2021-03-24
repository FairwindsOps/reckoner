// To see all options:
// https://vuepress.vuejs.org/config/
// https://vuepress.vuejs.org/theme/default-theme-config.html
module.exports = {
  title: "Reckoner Documentation",
  description: "Documentation for Fairwinds' Reckoner",
  themeConfig: {
    docsRepo: "FairwindsOps/reckoner",
    sidebar: [
      {
        title: "Reckoner",
        path: "/",
        sidebarDepth: 0,
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

