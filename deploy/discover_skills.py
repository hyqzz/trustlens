"""发现真实 Agent Skills——用 GitHub 公开搜索（无认证）找仓库，再取 tree 收集 SKILL.md。"""
import json
import time
import urllib.parse
import urllib.request


def get_json(url, pause=0):
    if pause:
        time.sleep(pause)
    req = urllib.request.Request(url, headers={"User-Agent": "trustlens-skills/0.1"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))


# 1. 仓库搜索：找包含 skills 的仓库（每类搜索取 Top N）
queries = [
    "claude-skills in:name,description",
    "agent-skills in:name",
    "skills SKILL.md in:readme",
    "claude skills marketplace in:description",
    "agent skills collection in:description",
    "opencode skills in:name,description",
]
repos = {}
for q in queries:
    try:
        d = get_json("https://api.github.com/search/repositories?q=" + urllib.parse.quote(q) +
                     "&sort=stars&order=desc&per_page=15", pause=7)
        for r in d.get("items", []):
            if r["stargazers_count"] >= 10:  # 只看有一定影响力的真实仓库
                repos[r["full_name"]] = {"full_name": r["full_name"], "stars": r["stargazers_count"],
                                         "desc": (r.get("description") or "")[:60]}
    except Exception as e:
        print(f"  搜索 {q} 失败: {e}")

print(f"搜索到 {len(repos)} 个候选仓库（≥10 star）：")
for n, v in sorted(repos.items(), key=lambda x: -x[1]["stars"])[:40]:
    print(f"  {v['stars']:>5}★ {n}  {v['desc']}")

# 2. 逐个取 tree，收集 SKILL.md
candidates = []
checked = 0
for full_name in sorted(repos, key=lambda n: -repos[n]["stars"])[:28]:
    owner, repo = full_name.split("/")
    checked += 1
    try:
        info = get_json(f"https://api.github.com/repos/{owner}/{repo}")
        branch = info.get("default_branch", "main")
        tree = get_json(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1")
        n = 0
        for item in tree.get("tree", []):
            p = item["path"]
            if p.lower().endswith("skill.md"):
                candidates.append({"repo": full_name,
                                   "skill": p.rsplit("/", 1)[0],
                                   "path": p,
                                   "url": f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{urllib.parse.quote(p)}"})
                n += 1
        print(f"  {full_name}: {n} 个 SKILL.md")
    except Exception as e:
        print(f"  {full_name}: 失败 {e}")

seen, uniq = set(), []
for c in candidates:
    k = (c["repo"], c["path"])
    if k not in seen:
        seen.add(k); uniq.append(c)
print(f"\n候选 Skills 总数（去重）: {len(uniq)}")
json.dump(uniq, open("data/skills-candidates.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
