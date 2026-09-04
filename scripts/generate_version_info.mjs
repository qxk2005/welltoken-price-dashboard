#!/usr/bin/env node

/**
 * WellToken Price Dashboard - 自动化版本与更新日志生成脚本
 * 
 * 作用：在每次打包编译或本地运行前执行，提取 package.json 版本号、Git Commit、
 * 构建时间戳，并将 CHANGELOG.md 解析为结构化数据，输出至前端内嵌模块中。
 */

import fs from 'node:fs'
import path from 'node:path'
import { execSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const rootDir = path.resolve(__dirname, '..')

// 1. 读取 package.json
const pkgPath = path.join(rootDir, 'package.json')
const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf-8'))
const version = pkg.version || '1.4.0'

// 2. 提取 Git 元数据
let gitCommit = 'unknown'
let gitBranch = 'main'
let gitDate = ''
try {
  gitCommit = execSync('git rev-parse --short HEAD', { cwd: rootDir, encoding: 'utf-8' }).trim()
  gitBranch = execSync('git rev-parse --abbrev-ref HEAD', { cwd: rootDir, encoding: 'utf-8' }).trim()
  gitDate = execSync('git log -1 --format=%cd --date=iso', { cwd: rootDir, encoding: 'utf-8' }).trim()
} catch (e) {
  // 非 git 环境或容错
  gitCommit = 'dev-' + Date.now().toString(16).slice(-6)
}

// 3. 构建时间戳
const now = new Date()
const buildTimeIso = now.toISOString()
const buildTimeFormatted = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`

// 4. 解析 CHANGELOG.md
const changelogPath = path.join(rootDir, 'CHANGELOG.md')
let changelogRaw = ''
if (fs.existsSync(changelogPath)) {
  changelogRaw = fs.readFileSync(changelogPath, 'utf-8')
}

function parseChangelog(markdown) {
  const versions = []
  if (!markdown) return versions

  // 按 ## 🚀 [v... 分割
  const versionBlocks = markdown.split(/^##\s+🚀\s+/m).slice(1)

  for (const block of versionBlocks) {
    const lines = block.split('\n')
    const firstLine = lines[0].trim()
    
    // 匹配 [v1.4.0 ...] - 2026-09-04
    const titleMatch = firstLine.match(/\[(v[\d\.]+(?:[^\].]+)?)\](?:\s*-\s*(\d{4}-\d{2}-\d{2}))?/)
    const verTag = titleMatch ? titleMatch[1] : firstLine
    const releaseDate = titleMatch && titleMatch[2] ? titleMatch[2] : ''

    // 提取纯净版本号 (如 1.4.0)
    const semverMatch = verTag.match(/v?(\d+\.\d+\.\d+)/)
    const semver = semverMatch ? semverMatch[1] : verTag

    // 提取主要分类条目
    const sections = []
    let currentSection = null
    const contentLines = lines.slice(1)

    for (const rawLine of contentLines) {
      const line = rawLine.trim()
      if (line.startsWith('### ')) {
        const secTitle = line.replace('### ', '').trim()
        currentSection = {
          title: secTitle,
          items: []
        }
        sections.push(currentSection)
      } else if (line.startsWith('- ') || line.startsWith('* ')) {
        const itemText = line.replace(/^[-*]\s+/, '').trim()
        if (currentSection) {
          currentSection.items.push(itemText)
        } else {
          if (sections.length === 0) {
            currentSection = { title: '主要变更', items: [] }
            sections.push(currentSection)
          }
          sections[0].items.push(itemText)
        }
      }
    }

    versions.push({
      version: semver,
      tag: verTag.startsWith('v') ? verTag : `v${verTag}`,
      fullTitle: firstLine,
      date: releaseDate,
      sections,
      rawContent: lines.slice(1).join('\n').trim()
    })
  }

  return versions
}

const changelog = parseChangelog(changelogRaw)

// 5. 组合完整的版本元数据
const versionData = {
  name: pkg.name || 'welltoken-price-dashboard',
  productName: pkg.build?.productName || 'WellToken Price Dashboard',
  version: version,
  fullVersion: `v${version}`,
  description: pkg.description || 'Token & Crypto Price Dashboard',
  author: pkg.author || 'qxk2005',
  homepage: pkg.homepage || 'https://github.com/qxk2005/welltoken-price-dashboard',
  git: {
    commit: gitCommit,
    branch: gitBranch,
    date: gitDate
  },
  build: {
    time: buildTimeFormatted,
    iso: buildTimeIso,
    node: process.version,
    platform: process.platform,
    arch: process.arch
  },
  changelog: changelog,
  latestChangelog: changelog[0] || null
}

// 6. 写入目标文件
const outputDir = path.join(rootDir, 'src', 'renderer', 'src', 'generated')
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true })
}

const jsonFile = path.join(outputDir, 'version_info.json')
fs.writeFileSync(jsonFile, JSON.stringify(versionData, null, 2), 'utf-8')

const tsFile = path.join(outputDir, 'version_info.ts')
fs.writeFileSync(
  tsFile,
  `// 自动生成于编译构建阶段，请勿手动修改
import versionInfoRaw from './version_info.json'

export interface ChangelogSection {
  title: string
  items: string[]
}

export interface ChangelogEntry {
  version: string
  tag: string
  fullTitle: string
  date: string
  sections: ChangelogSection[]
  rawContent: string
}

export interface VersionInfo {
  name: string
  productName: string
  version: string
  fullVersion: string
  description: string
  author: string
  homepage: string
  git: {
    commit: string
    branch: string
    date: string
  }
  build: {
    time: string
    iso: string
    node: string
    platform: string
    arch: string
  }
  changelog: ChangelogEntry[]
  latestChangelog: ChangelogEntry | null
}

export const versionInfo: VersionInfo = versionInfoRaw as unknown as VersionInfo
export default versionInfo
`,
  'utf-8'
)

console.log(`✅ [Version Generator] 成功生成版本元数据 -> v${version} (Git: ${gitCommit}, Changelog 版本数: ${changelog.length})`)
