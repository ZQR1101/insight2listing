import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17201d",
        canvas: "#f6f7f3",
        line: "#e5e8e1",
        moss: "#285c48",
        mint: "#dcece3",
        amber: "#c87536",
      },
      boxShadow: {
        panel: "0 1px 2px rgba(21, 34, 29, 0.04), 0 10px 30px rgba(21, 34, 29, 0.04)",
        float: "0 18px 60px rgba(20, 31, 27, 0.14)",
      },
    },
  },
  plugins: [],
};

export default config;
