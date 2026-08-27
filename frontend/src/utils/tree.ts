export interface FileNode {
  name: string
  path: string
  type: 'file' | 'folder'
  children?: FileNode[]
}

/**
 * Builds a hierarchical tree structure from a flat array of file paths.
 * Sorts nodes with folders first (alphabetical) followed by files (alphabetical).
 */
export function buildFileTree(paths: string[]): FileNode[] {
  const root: FileNode[] = []

  paths.forEach((fullPath) => {
    // Standardize path slashes to forward slashes
    const normalizedPath = fullPath.replace(/\\/g, '/')
    const parts = normalizedPath.split('/').filter(Boolean)
    let currentLevel = root

    parts.forEach((part, index) => {
      const isLast = index === parts.length - 1
      const type = isLast ? 'file' : 'folder'
      const accumulatedPath = parts.slice(0, index + 1).join('/')

      // Search for existing node in current level
      let existingNode = currentLevel.find((node) => node.name === part && node.type === type)

      if (!existingNode) {
        existingNode = {
          name: part,
          path: accumulatedPath,
          type,
        }
        if (type === 'folder') {
          existingNode.children = []
        }
        currentLevel.push(existingNode)
      }

      if (type === 'folder' && existingNode.children) {
        currentLevel = existingNode.children
      }
    })
  })

  // Recursive sorter helper: Folders first, then files, both alphabetically
  const sortTreeNodes = (nodes: FileNode[]): FileNode[] => {
    return nodes
      .sort((a, b) => {
        if (a.type !== b.type) {
          return a.type === 'folder' ? -1 : 1
        }
        return a.name.localeCompare(b.name)
      })
      .map((node) => {
        if (node.type === 'folder' && node.children) {
          node.children = sortTreeNodes(node.children)
        }
        return node
      })
  }

  return sortTreeNodes(root)
}
