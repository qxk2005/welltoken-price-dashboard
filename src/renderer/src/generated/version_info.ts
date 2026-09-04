// 自动生成于编译构建阶段，请勿手动修改
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
