import path from "path";
import type { NextConfig } from "next";
import { fileURLToPath } from "url";

const workspaceRoot = path.dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  output: "standalone",
  turbopack: {
    root: workspaceRoot,
  },
};

export default nextConfig;
