export default {
  title: "wow-agent",
  url: "https://uuzjw.github.io/wow-agent/",
  description:
    "Terminal Coding Agent for Everyone — a simple, open, extensible terminal AI coding assistant. 模型自由、本地运行、安全可控。",
  language: "en",
  permalinkStyle: "post-name",
  basePath: "/wow-agent",
  theme: "wow",
  paginationSize: 5,
  redirects: {
    "/zh/": "/zh/home/",
  },
  seo: {
    siteName: "wow-agent",
    defaultDescription:
      "A simple, open, extensible terminal AI coding assistant. Model freedom, local-first, safety by default.",
    favicon: "/assets/favicon.png",
    defaultOgImage: "/assets/og-default.png",
    defaultOgImageAlt: "wow-agent - Terminal Coding Agent for Everyone",
    themeColor: "#1d4ed8",
    robotsTxt: `User-agent: *
Allow: /
Sitemap: http://localhost:3000/sitemap.xml
`,
    organization: {
      name: "wow-agent",
      sameAs: ["https://github.com/uuzjw/wow-agent"],
    },
  },
  menus: {
    primary: [],
    footer: [
      { text: "GitHub", url: "https://github.com/uuzjw/wow-agent" },
    ],
  },
  socialLinks: [
    {
      text: "GitHub",
      url: "https://github.com/uuzjw/wow-agent",
      rel: "noopener noreferrer",
      target: "_blank",
    },
  ],
  plugins: [],
  deploy: {
    github: { repo: "uuzjw/wow-agent", branch: "gh-pages", cname: "" },
    vercel: { project: "", prod: true },
  },
};
