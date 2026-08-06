import { useState } from "react";
import type { FileTreeNode } from "../types/api";

type Props = {
  nodes: FileTreeNode[];
  selectedPath?: string | null;
  onSelectFile?: (path: string) => void;
};

export function FileTree({ nodes, selectedPath, onSelectFile }: Props) {
  return (
    <ul className="space-y-0.5 font-mono text-[12px]">
      {nodes.map((node) => (
        <TreeNode
          key={node.path}
          node={node}
          depth={0}
          selectedPath={selectedPath}
          onSelectFile={onSelectFile}
        />
      ))}
    </ul>
  );
}

function TreeNode({
  node,
  depth,
  selectedPath,
  onSelectFile,
}: {
  node: FileTreeNode;
  depth: number;
  selectedPath?: string | null;
  onSelectFile?: (path: string) => void;
}) {
  const [open, setOpen] = useState(depth < 1);
  const isFolder = node.type === "folder";
  const active = selectedPath === node.path;

  return (
    <li>
      <button
        type="button"
        onClick={() => {
          if (isFolder) {
            setOpen((v) => !v);
            return;
          }
          onSelectFile?.(node.path);
        }}
        className={`flex w-full items-center gap-2 rounded-lg px-2 py-1 text-left transition ${
          active ? "bg-accent/15 text-accent-soft" : "hover:bg-white/5"
        }`}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
      >
        <span className="w-3 shrink-0 text-white/35">{isFolder ? (open ? "▾" : "▸") : "·"}</span>
        <span className={`truncate ${isFolder ? "text-white/70" : "text-white/85"}`}>{node.name}</span>
        {isFolder && <span className="ml-auto shrink-0 text-[10px] text-white/30">{node.file_count ?? 0}</span>}
        {!isFolder && node.language && (
          <span className="ml-auto shrink-0 text-[10px] text-white/30">{node.language}</span>
        )}
      </button>
      {isFolder && open && node.children && (
        <ul>
          {node.children.map((child) => (
            <TreeNode
              key={child.path}
              node={child}
              depth={depth + 1}
              selectedPath={selectedPath}
              onSelectFile={onSelectFile}
            />
          ))}
        </ul>
      )}
    </li>
  );
}
