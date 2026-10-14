"use strict";
const data = JSON.parse(document.getElementById("gallery-data").textContent);
const app = document.getElementById("app");
const dialog = document.getElementById("lightbox");
const largeImage = document.getElementById("large-image");
const stage = document.getElementById("image-stage");
const info = document.getElementById("lightbox-info");
const viewerMain = document.getElementById("lightbox-main");
const STRINGS = {
  zh: {
    htmlLang: "zh-CN", toggle: "EN", toggleLabel: "Switch to English",
    footer: "Whale-chan · 每个灵感，都有迹可循。",
    lightbox: "图片预览", fit: "适应", imageDetails: "图片详情",
    closeLabel: "关闭预览", previous: "上一张 (←)", next: "下一张 (→)",
    zoomIn: "放大 (+)", zoomOut: "缩小 (−)", zoomToggle: "适应窗口 ↔ 100% (Z)",
    compare: "对照原图", compareTitle: "对照输入原图 (S)", detailsTitle: "图片详情 (I)", closeTitle: "关闭 (Esc)",
    collection: "当前集合", sourceInput: "输入原图",
    viewerHint: "滚轮缩放 · 拖动平移 · 单击 适应↔100% · ← → 切换 · S 对照原图 · I 详情 · Esc 关闭",
    notRecorded: "未记录",
    roles: {candidate: "整图候选"},
    refRoles: {identity: "角色身份", style: "画风", proportion: "比例", typography: "文字样式", composition: "构图", costume: "服装", background: "背景", pose_action: "动作"},
    pictures: {candidate: "{label} 候选", source: "输入原图 {label}", reference: "{label}", final: "{label}"},
    reference: "参考图",
    records: {visual_qa: "验收", automatic_qa: "自动验收", prompt: "提示词"},
    warnings: {image_missing: "{subject}：图片文件缺失", record_missing: "{subject} {record}：记录缺失",
               final_ambiguous: "{subject}：多个候选与成品哈希相同，无法唯一确定提示词；请查看生成过程",
               final_unrecorded: "{subject}：成品来源记录缺失"},
    prompt: "实际生图提示词", copyPrompt: "复制提示词", copied: "已复制", selectToCopy: "已选中，请按 ⌘C / Ctrl+C 复制",
    originUnknown: "成品来源未能唯一确认，请查看生成过程。",
    collectionQA: "集合审阅与返工记录", minorIssues: "已接受的轻微瑕疵", outcomes: "任务状态与计时",
    qa: "验收记录", qaLine: "自动检查：{automatic} · 视觉检查：{visual}", failUnknown: "失败原因未记录", retry: "修正建议：{retry}",
    imageMissing: "图片文件缺失", noFinal: "尚无通过验收的成品", enlarge: "放大 {label}",
    passed: "已通过", failed: "未通过", notProduced: "未产出", calls: "产图 {n} 次",
    tier: "档位 {tier}", tierContrast: "档位 {tier}（{axes}→{lowered}）", axisJoin: "、",
    history: "生成过程 · {calls} 次产图 · {errors} 次接口错误", noAttempts: "没有产图记录", final: "成品",
    sameAsFinal: "与成品哈希相同，但来源记录不唯一；不指定某次提示词为成品来源。",
    noImageErrors: "无图错误记录 · {n}", imageN: "图片 {n}",
    verdictPass: "通过", verdictFail: "未通过", verdictNone: "验收未记录", finalTwin: "成品同图 · 来源不唯一",
    noImages: "没有可展示的图片，记录见下方。", proposalRecords: "方案与记录",
    filterLabel: "漫画筛选", filterFinals: "已通过成品", filterAttempts: "尝试版本", filterAll: "全部",
    shownImages: "漫画 · {n} 张", viewHistory: "查看此创意的生成过程", showAllIdeas: "返回全部创意",
    ideaHistory: "生成过程：{title}", noFinalImages: "暂无通过成品。", noAttemptImages: "没有可展示的尝试版本。",
    viewAttempts: "查看尝试版本", finalOriginAmbiguous: "成品来源记录不唯一；生成过程保留全部同图记录。",
    selectedProposal: "入选方案", unselectedProposal: "未入选方案",
    imageSummary: "{name} · {calls} 次出图 · {errors} 次无图错误", attemptMissing: "{id}：图片文件缺失",
    startingPoint: "创作起点",
    groupStats: "{passed} / {planned} 张已通过 · 产图 {calls} 次 · {errors} 次接口错误 · {date}",
    request: "用户原始要求", noRequest: "未记录用户原始文字要求。",
    analysis: "素材转述 · 非用户原话", references: "角色与视觉参考图 · {n} 张", recordNotes: "记录提示 · {n}",
    expand: "展开全文", collapse: "收起",
    allImages: "全部图片 · {n}", proposalsWorks: "方案与作品 · {n}", grid: "▦ 网格", list: "☰ 列表",
    notGenerated: "未生成", proposalPassed: "{passed} / {planned} 张已通过",
    titleComic: "鲸鱼娘 · 漫画图册", titleCharacter: "鲸鱼娘 · 角色图册",
    statSources: "素材 / 主题", statFinals: "交付成品", statCalls: "产图次数",
    tabsLabel: "素材组或创作主题", tabsHeading: "素材组 · {n}", switchGroups: "切换",
    tabMeta: "{passed}/{planned} 已通过 · 产图 {calls} 次", groupPager: "切换素材组",
    inputOrReference: "输入素材或视觉参考图",
  },
  en: {
    htmlLang: "en", toggle: "中文", toggleLabel: "切换到中文",
    footer: "Whale-chan · Every idea leaves a trail.",
    lightbox: "Image preview", fit: "Fit", imageDetails: "Details",
    closeLabel: "Close preview", previous: "Previous (←)", next: "Next (→)",
    zoomIn: "Zoom in (+)", zoomOut: "Zoom out (−)", zoomToggle: "Fit window ↔ 100% (Z)",
    compare: "Compare source", compareTitle: "Show the input image alongside (S)", detailsTitle: "Image details (I)", closeTitle: "Close (Esc)",
    collection: "Current collection", sourceInput: "Input image",
    viewerHint: "Scroll to zoom · drag to pan · click for fit↔100% · ← → browse · S source · I details · Esc close",
    notRecorded: "Not recorded",
    roles: {candidate: "Full-canvas candidate"},
    refRoles: {identity: "Identity", style: "Style", proportion: "Proportion", typography: "Typography", composition: "Composition", costume: "Costume", background: "Background", pose_action: "Pose & action"},
    pictures: {candidate: "{label} candidate", source: "Input image {label}", reference: "{label}", final: "{label}"},
    reference: "Reference",
    records: {visual_qa: "visual QA", automatic_qa: "automatic QA", prompt: "prompt"},
    warnings: {image_missing: "{subject}: image file missing", record_missing: "{subject} {record}: record missing",
               final_ambiguous: "{subject}: several candidates match the final's hash, so its prompt cannot be identified; see the generation history",
               final_unrecorded: "{subject}: the final's source record is missing"},
    prompt: "Prompt sent to the provider", copyPrompt: "Copy prompt", copied: "Copied", selectToCopy: "Selected — press ⌘C / Ctrl+C to copy",
    originUnknown: "The final's source attempt could not be identified uniquely; see the generation history.",
    qa: "QA record", qaLine: "Automatic: {automatic} · Visual: {visual}", failUnknown: "Failure reason not recorded", retry: "Suggested fix: {retry}",
    imageMissing: "Image file missing", noFinal: "No passing final yet", enlarge: "Enlarge {label}",
    passed: "Passed", failed: "Failed", notProduced: "Not produced", calls: "{n} image call(s)",
    tier: "Tier {tier}", tierContrast: "Tier {tier} ({axes}→{lowered})", axisJoin: ", ",
    history: "Generation history · {calls} image call(s) · {errors} provider error(s)", noAttempts: "No image-producing attempts", final: "Final",
    sameAsFinal: "Same hash as the final, but its source is ambiguous; no prompt is credited as the final's source.",
    noImageErrors: "Errors without images · {n}", imageN: "Image {n}",
    verdictPass: "Passed", verdictFail: "Failed", verdictNone: "QA not recorded", finalTwin: "Same as final · source ambiguous",
    noImages: "No images to show; see the records below.", proposalRecords: "Proposals and records",
    filterLabel: "Filter comics", filterFinals: "Passed finals", filterAttempts: "Attempts", filterAll: "All",
    shownImages: "Comics · {n} images", viewHistory: "View this idea’s generation history", showAllIdeas: "Back to all ideas",
    ideaHistory: "Generation history: {title}", noFinalImages: "No passing finals yet.", noAttemptImages: "No attempt images to show.",
    viewAttempts: "View attempts", finalOriginAmbiguous: "The final’s source record is ambiguous; all matching records remain in its history.",
    selectedProposal: "Selected", unselectedProposal: "Not selected",
    imageSummary: "{name} · {calls} image call(s) · {errors} error(s) without images", attemptMissing: "{id}: image file missing",
    startingPoint: "STARTING POINT",
    groupStats: "{passed} / {planned} passed · {calls} image call(s) · {errors} provider error(s) · {date}",
    request: "Original request", noRequest: "No written request was recorded.",
    collectionQA: "Collection reviews and repairs", minorIssues: "Accepted minor issues", outcomes: "Task outcomes and timing",
    analysis: "Source transcription · not the user's words", references: "Character and visual references · {n}", recordNotes: "Record notes · {n}",
    expand: "Show all", collapse: "Show less",
    allImages: "All images · {n}", proposalsWorks: "Proposals and works · {n}", grid: "▦ Grid", list: "☰ List",
    notGenerated: "Not generated", proposalPassed: "{passed} / {planned} passed",
    titleComic: "Whale-chan · Comic Gallery", titleCharacter: "Whale-chan · Character Gallery",
    statSources: "Sources / themes", statFinals: "Finals delivered", statCalls: "Image calls",
    tabsLabel: "Source groups or themes", tabsHeading: "Sources · {n}", switchGroups: "switch",
    tabMeta: "{passed}/{planned} passed · {calls} call(s)", groupPager: "Switch source group",
    inputOrReference: "Input material or visual reference",
  },
};
function storedLanguage() {
  try { return localStorage.getItem("whalechan-gallery-language"); } catch { return null; }
}
let language = [storedLanguage(), data.language].find(value => value in STRINGS) || "zh";
let activeGroup = 0, view = "grid", currentGroup = null, currentPictures = [], currentIndex = 0, opener;
const comicFilters = new Map();
function t(key, values = {}) {
  return String(STRINGS[language][key]).replace(/\{(\w+)\}/g, (match, name) => name in values ? values[name] : match);
}
function format(template, values) { return template.replace(/\{(\w+)\}/g, (match, name) => name in values ? values[name] : match); }
function pad(number) { return String(number).padStart(2, "0"); }
function pictureName(picture) {
  if (!picture) return "";
  if (picture.kind === "reference" && !picture.label) return t("reference");
  return format(STRINGS[language].pictures[picture.kind] || "{label}", {label: picture.label});
}
function warningText(warning) {
  const subject = typeof warning.subject === "object" ? pictureName(warning.subject) : warning.subject;
  return format(STRINGS[language].warnings[warning.code] || warning.code,
                {subject, record: STRINGS[language].records[warning.record] || ""});
}
function tierText(tier) {
  if (!tier) return "";
  if (!tier.axes) return t("tier", {tier: tier.tier});
  return t("tierContrast", {tier: tier.tier, lowered: tier.lowered_to,
                            axes: tier.axes.map(axis => axis[language] || axis.en).join(t("axisJoin"))});
}
function roleName(role) { return STRINGS[language].roles[role] || role; }
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function button(text, action) {
  const node = el("button", "", text);
  node.type = "button";
  node.addEventListener("click", action);
  return node;
}
function details(title) {
  const node = el("details");
  node.append(el("summary", "", title));
  return node;
}
function text(value) { return value == null || value === "" ? t("notRecorded") : typeof value === "string" ? value : JSON.stringify(value, null, 2); }
function badge(value, kind = "") { return el("span", `badge ${kind}`, value); }
function date(value) { return value ? value.replace("T", " ").replace(/\.\d+/, "") : t("notRecorded"); }
function thumbnail(src, className) {
  const img = el("img", className);
  img.src = src; img.alt = ""; img.loading = "lazy"; img.decoding = "async";
  return img;
}
function promptBlock(value) {
  const block = details(t("prompt"));
  if (!value) { block.append(el("p", "muted", t("notRecorded"))); return block; }
  const area = el("textarea", "prompt");
  area.value = value;
  area.readOnly = true;
  area.setAttribute("aria-label", t("prompt"));
  const status = el("span", "copy-status");
  status.setAttribute("role", "status");
  const copy = button(t("copyPrompt"), async () => {
    try {
      await navigator.clipboard.writeText(value);
      status.textContent = t("copied");
    } catch {
      area.focus(); area.select();
      status.textContent = t("selectToCopy");
    }
  });
  block.append(area, copy, status);
  return block;
}
function attemptInfo(attempt) {
  const box = el("div");
  if (!attempt) { box.append(el("p", "muted", t("originUnknown"))); return box; }
  const meta = el("div", "meta");
  meta.append(badge(roleName(attempt.role)), badge(attempt.verdict || t("notRecorded"), attempt.verdict === "PASS" ? "good" : "warn"));
  box.append(meta);
  box.append(el("p", "note", `${text(attempt.provider)} / ${text(attempt.model)}`), promptBlock(attempt.prompt));
  box.append(el("p", "note", t("recordedAt", {date: date(attempt.created_at)})));
  const qa = details(t("qa"));
  qa.append(el("p", "", t("qaLine", {automatic: text(attempt.automatic), visual: text(attempt.visual)})));
  if (attempt.defects?.length) qa.append(el("p", "", text(attempt.defects)));
  if (attempt.verdict === "FAIL" && !attempt.defects?.length) qa.append(el("p", "muted", t("failUnknown")));
  if (attempt.minor_issues?.length) qa.append(el("p", "", `${t("minorIssues")}: ${text(attempt.minor_issues)}`));
  if (attempt.targeted_retry) qa.append(el("p", "", t("retry", {retry: text(attempt.targeted_retry)})));
  box.append(qa);
  return box;
}
function imageButton(picture, collection, detailFactory, title) {
  if (!picture?.src) return el("div", "missing", picture ? t("imageMissing") : t("noFinal"));
  const entry = {picture, detailFactory, title, group: currentGroup};
  collection.push(entry);
  const node = button("", () => openLightbox(collection, collection.indexOf(entry), node));
  node.className = "picture";
  node.setAttribute("aria-label", t("enlarge", {label: title || pictureName(picture)}));
  const img = thumbnail(picture.src);
  img.alt = title || pictureName(picture);
  node.append(img);
  return node;
}
function sourceStrip(pictures) {
  const strip = el("div", "source-strip");
  const collection = [];
  pictures.forEach(picture => {
    const figure = el("figure", "figure");
    figure.append(imageButton(picture, collection), el("figcaption", "", pictureName(picture)));
    if (picture.roles) figure.append(el("figcaption", "", picture.roles.map(role => STRINGS[language].refRoles[role] || role).join(" · ")));
    strip.append(figure);
  });
  return strip;
}
function card(image, collection) {
  const article = el("article", "card");
  article.append(imageButton(image.final, collection, () => attemptInfo(image.origin)));
  const body = el("div", "card-content");
  body.append(el("h3", "", image.name));
  const meta = el("div", "meta");
  const delivered = image.status === "passed";
  meta.append(badge(delivered ? t("passed") : image.calls ? t("failed") : t("notProduced"), delivered ? "good" : "warn"), badge(t("calls", {n: image.calls})));
  if (image.tier) meta.append(badge(tierText(image.tier)));
  body.append(meta);
  if (image.note) body.append(el("p", "note", image.note));
  if (delivered) body.append(attemptInfo(image.origin));
  const history = details(t("history", {calls: image.calls, errors: image.errors.length}));
  const candidates = [];
  image.attempts.forEach(attempt => {
    const section = el("div", "attempt");
    section.append(el("p", "note", `${attempt.id} · ${roleName(attempt.role)}`));
    section.append(imageButton(attempt.picture, candidates, () => attemptInfo(attempt)), attemptInfo(attempt));
    history.append(section);
  });
  if (!image.attempts.length) history.append(el("p", "muted", t("noAttempts")));
  image.errors.forEach(error => {
    const section = el("div", "attempt");
    section.append(el("p", "", `${text(error.provider)} / ${text(error.model)} · ${text(error.category)}`), el("p", "muted", text(error.details)), el("p", "muted", date(error.created_at)));
    history.append(section);
  });
  body.append(history); article.append(body);
  return article;
}
function galleryImageInfo(item) {
  const box = el("div");
  box.append(el("h3", "", item.proposal_title),
             el("p", "note", [item.scene, item.detail].filter(Boolean).join(" · ")),
             el("p", "note", `${item.image_name} · ${item.attempt?.id || t("final")}`));
  if (item.tier) {
    const meta = el("div", "meta");
    meta.append(badge(tierText(item.tier))); box.append(meta);
  }
  if (item.note) box.append(el("p", "note", item.note));
  if (item.matches_final && !item.is_final) {
    box.append(el("p", "note", t("sameAsFinal")));
  }
  if (item.origin_ambiguous) box.append(el("p", "note", t("finalOriginAmbiguous")));
  box.append(attemptInfo(item.attempt));
  if (item.errors.length) {
    const errors = details(t("noImageErrors", {n: item.errors.length}));
    item.errors.forEach(error => errors.append(
      el("p", "", `${text(error.provider)} / ${text(error.model)} · ${text(error.category)}`),
      el("p", "muted", text(error.details)), el("p", "muted", date(error.created_at))));
    box.append(errors);
  }
  return box;
}
function galleryImageCard(item, collection, showHistory) {
  const article = el("article", "card gallery-image");
  article.append(imageButton(item.picture, collection, () => galleryImageInfo(item), item.proposal_title));
  const body = el("div", "card-content"), meta = el("div", "meta");
  body.append(el("h3", "", item.proposal_title));
  const verdict = item.attempt?.verdict;
  if (item.is_final) meta.append(badge(t("final"), "good"));
  else meta.append(badge(verdict === "PASS" ? t("verdictPass") : verdict === "FAIL" ? t("verdictFail") : t("verdictNone"),
                         verdict === "PASS" ? "good" : "warn"));
  if (!item.is_final && item.matches_final) meta.append(badge(t("finalTwin"), "warn"));
  if (item.attempt) {
    meta.append(badge(item.attempt.id));
    if (item.attempt.role !== "candidate") meta.append(badge(roleName(item.attempt.role)));
  }
  if (item.tier) meta.append(badge(tierText(item.tier)));
  body.append(meta);
  if (item.scene) body.append(el("p", "card-scene", item.scene));
  if (item.is_final && showHistory) {
    const history = button(t("viewHistory"), () => showHistory(item.image_id));
    history.className = "link-button"; body.append(history);
  }
  article.append(body);
  return article;
}
function comicCollections(group) {
  const contexts = new Map();
  group.proposals.forEach(proposal => proposal.images.forEach(image => contexts.set(image.id, {proposal, image})));
  function contextualize(entry) {
    const {proposal, image} = contexts.get(entry.image_id);
    return {...entry, image_name: image.name, proposal_title: proposal.title,
                  scene: proposal.scene, detail: proposal.detail, note: image.note, tier: image.tier,
                  attempt: entry.attempt_index == null ? image.origin : image.attempts[entry.attempt_index],
                  attempts: image.attempts, errors: image.errors};
  }
  const all = group.gallery_images.map(contextualize);
  const finals = [];
  contexts.forEach(({image}) => {
    if (image.status !== "passed") return;
    const matched = all.find(item => item.image_id === image.id && item.matches_final);
    const picture = image.final?.src ? image.final : matched?.picture;
    if (!picture?.src) return;
    finals.push({...contextualize({image_id: image.id, picture, attempt_index: null,
                                  is_final: true, matches_final: true}),
                 origin_ambiguous: !image.origin && Boolean(matched?.attempt)});
  });
  return {finals, attempts: all.filter(item => !item.is_final), all};
}
function renderComicImages(group, panel, heading, slot) {
  const sets = comicCollections(group);
  if (!comicFilters.has(group)) comicFilters.set(group, {mode: "finals", imageId: null});
  const state = comicFilters.get(group);
  const browser = el("section", "comic-browser");
  const modes = [["finals", "filterFinals"], ["attempts", "filterAttempts"], ["all", "filterAll"]];
  function render(focus = false) {
    browser.replaceChildren();
    const scoped = items => state.imageId ? items.filter(item => item.image_id === state.imageId) : items;
    const filters = el("div", "controls comic-filters");
    filters.setAttribute("role", "group"); filters.setAttribute("aria-label", t("filterLabel"));
    modes.forEach(([mode, label]) => {
      const control = button(`${t(label)} · ${scoped(sets[mode]).length}`, () => {
        state.mode = mode; render(true);
      });
      control.setAttribute("aria-pressed", String(state.mode === mode)); filters.append(control);
    });
    slot.replaceChildren(filters);
    if (state.imageId) {
      const item = sets.all.find(item => item.image_id === state.imageId) || sets.finals.find(item => item.image_id === state.imageId);
      const context = el("div", "history-context");
      context.append(el("p", "", t("ideaHistory", {title: item.proposal_title})), button(t("showAllIdeas"), () => {
        state.imageId = null; state.mode = "finals"; render(true);
      }));
      browser.append(context);
    }
    const items = scoped(sets[state.mode]), cards = el("div", "cards gallery-images"), collection = [];
    heading.textContent = t("shownImages", {n: items.length});
    items.forEach(item => cards.append(galleryImageCard(item, collection, state.imageId ? null : imageId => {
      state.imageId = imageId; state.mode = "all"; render(true);
      heading.scrollIntoView({block: "start"});
    })));
    browser.append(cards);
    if (!items.length) {
      const empty = el("div", "empty");
      empty.append(el("p", "", t(state.mode === "finals" ? "noFinalImages" : state.mode === "attempts" ? "noAttemptImages" : "noImages")));
      if (state.mode === "finals" && scoped(sets.attempts).length) empty.append(button(t("viewAttempts"), () => {
        state.mode = "attempts"; render(true);
      }));
      browser.append(empty);
    }
    if (focus) filters.querySelector('[aria-pressed="true"]').focus();
  }
  panel.append(browser); render();
  const records = details(t("proposalRecords"));
  records.className = "proposal-records";
  group.proposals.forEach(proposal => {
    const summary = details(proposal.title);
    summary.append(el("p", "note", proposal.selected ? t("selectedProposal") : t("unselectedProposal")),
                   el("p", "", proposal.scene), el("p", "muted", proposal.detail));
    proposal.images.forEach(image => {
      summary.append(el("p", "note", t("imageSummary", {name: image.name, calls: image.calls, errors: image.errors.length})));
      image.errors.forEach(error => summary.append(el("p", "muted", `${text(error.category)} · ${text(error.details)}`)));
      image.attempts.filter(attempt => !attempt.picture?.src).forEach(attempt => {
        summary.append(el("p", "muted", t("attemptMissing", {id: attempt.id})), attemptInfo(attempt));
      });
    });
    records.append(summary);
  });
  panel.append(records);
}
function sourceText(label, value, clamp) {
  const box = el("div", "source-block");
  box.append(el("p", "section-label", label));
  const body = el("p", "source-text", value);
  box.append(body);
  if (clamp && value.length > 160) {
    body.classList.add("clamped");
    const toggle = button(t("expand"), () => {
      const open = body.classList.toggle("clamped");
      toggle.textContent = open ? t("expand") : t("collapse");
    });
    toggle.className = "link-button"; box.append(toggle);
  }
  return box;
}
function renderGroup(group, panel) {
  panel.replaceChildren();
  currentGroup = group;
  const index = data.groups.indexOf(group);
  const source = el("section", "source");
  if (group.originals.length) { source.classList.add("with-originals"); source.append(sourceStrip(group.originals)); }
  const about = el("div", "source-info");
  about.append(el("div", "section-label", `${t("startingPoint")} · ${pad(index + 1)} / ${pad(data.groups.length)}`), el("h2", "", group.title));
  about.append(el("p", "source-stats", t("groupStats", {passed: group.passed, planned: group.planned, calls: group.calls, errors: group.errors, date: date(group.date)})));
  if (group.request) about.append(sourceText(t("request"), group.request, true));
  else about.append(el("p", "note", t("noRequest")));
  const records = el("div", "source-records");
  if (group.analysis && !group.request) about.append(sourceText(t("analysis"), group.analysis, true));
  else if (group.analysis) {
    const analysis = details(t("analysis"));
    analysis.append(el("p", "source-text", group.analysis)); records.append(analysis);
  }
  if (group.references.length) {
    const refs = details(t("references", {n: group.references.length}));
    refs.append(sourceStrip(group.references)); records.append(refs);
  }
  if (group.warnings.length) {
    const warnings = details(t("recordNotes", {n: group.warnings.length}));
    warnings.classList.add("warnings");
    group.warnings.forEach(warning => warnings.append(el("p", "", warningText(warning))));
    records.append(warnings);
  }
  if (group.selection_review) {
    const selection = details(language === "zh" ? "创意优先级与选择说明" : "Idea priority and selection");
    selection.append(el("p", "", group.selection_review.selection_reason));
    const ranking = el("ol");
    group.selection_review.ranking.forEach(item => ranking.append(el("li", "", `${item.idea_id}: ${item.reason}`)));
    selection.append(ranking);
    records.append(selection);
  }
  if (group.collection_reviews?.length) {
    const collection = details(t("collectionQA"));
    group.collection_reviews.forEach(item => {
      collection.append(sourceStrip([item.picture]));
      collection.append(el("pre", "source-text", JSON.stringify(item.review, null, 2)));
    });
    records.append(collection);
  }
  if (group.stage_events?.length) {
    const outcomes = details(t("outcomes"));
    outcomes.append(el("pre", "source-text", JSON.stringify({tasks: group.task_outcomes, events: group.stage_events}, null, 2)));
    records.append(outcomes);
  }
  if (records.childElementCount) about.append(records);
  source.append(about);
  panel.append(source);
  const toolbar = el("div", "toolbar");
  const heading = el("h2", "", data.skill === "comic"
    ? t("allImages", {n: group.gallery_images.length}) : t("proposalsWorks", {n: group.proposals.length}));
  heading.setAttribute("aria-live", "polite");
  const slot = el("div", "filter-slot");
  const controls = el("div", "controls view-toggle");
  const modes = [];
  for (const [mode, label] of [["grid", t("grid")], ["list", t("list")]]) {
    const control = button(label, () => {
      view = mode; panel.classList.toggle("list", view === "list");
      modes.forEach(([key, node]) => node.setAttribute("aria-pressed", String(key === view)));
    });
    control.setAttribute("aria-pressed", String(view === mode));
    modes.push([mode, control]); controls.append(control);
  }
  toolbar.append(heading, slot, controls); panel.append(toolbar);
  panel.classList.toggle("list", view === "list");
  if (data.skill === "comic") renderComicImages(group, panel, heading, slot);
  else group.proposals.forEach(proposal => {
    if (!proposal.selected) {
      const folded = details(""); folded.className = "unselected";
      folded.firstChild.append(el("span", "letter", proposal.choice), el("span", "", proposal.title), badge(t("notGenerated")));
      folded.append(el("p", "", proposal.scene), el("p", "muted", proposal.detail)); panel.append(folded); return;
    }
    const section = el("section", "proposal");
    const heading = el("div", "proposal-heading");
    const passed = proposal.images.filter(image => image.status === "passed").length;
    heading.append(el("span", "letter", proposal.choice), el("h3", "", proposal.title), badge(t("proposalPassed", {passed, planned: proposal.planned})));
    section.append(heading, el("p", "proposal-desc", [proposal.scene, proposal.detail].filter(Boolean).join(" · ")));
    const cards = el("div", "cards"), collection = [];
    proposal.images.forEach(image => cards.append(card(image, collection)));
    section.append(cards); panel.append(section);
  });
  panel.append(groupPager(index));
}
function groupPager(index) {
  const pager = el("nav", "group-pager");
  pager.setAttribute("aria-label", t("groupPager"));
  const last = data.groups.length - 1;
  const previous = button(`← ${index > 0 ? data.groups[index - 1].title : ""}`, () => selectGroup(index - 1, true));
  const next = button(`${index < last ? data.groups[index + 1].title : ""} →`, () => selectGroup(index + 1, true));
  previous.disabled = index === 0; next.disabled = index === last;
  pager.append(previous, el("span", "", `${pad(index + 1)} / ${pad(data.groups.length)}`), next);
  return pager;
}
function groupThumb(group) {
  return group.originals.find(picture => picture.src)
    || group.proposals.flatMap(proposal => proposal.images).map(image => image.final).find(picture => picture?.src);
}
let tabButtons = [], tabList, panel;
function revealTab(tab) {
  if (!tab || !tabList) return;
  const box = tabList.getBoundingClientRect(), rect = tab.getBoundingClientRect();
  if (tabList.scrollHeight > tabList.clientHeight) {
    if (rect.top < box.top) tabList.scrollTop += rect.top - box.top - 12;
    else if (rect.bottom > box.bottom) tabList.scrollTop += rect.bottom - box.bottom + 12;
  }
  if (tabList.scrollWidth > tabList.clientWidth) {
    if (rect.left < box.left) tabList.scrollLeft += rect.left - box.left - 12;
    else if (rect.right > box.right) tabList.scrollLeft += rect.right - box.right + 12;
  }
}
function selectGroup(index, fromUser = false) {
  if (index < 0 || index >= data.groups.length) return;
  activeGroup = index;
  tabButtons.forEach((tab, i) => { tab.setAttribute("aria-selected", String(i === index)); tab.tabIndex = i === index ? 0 : -1; });
  panel.setAttribute("aria-labelledby", tabButtons[index].id);
  renderGroup(data.groups[index], panel);
  revealTab(tabButtons[index]);
  if (fromUser && panel.getBoundingClientRect().top < 0) panel.scrollIntoView({block: "start"});
}
function renderStatic() {
  document.documentElement.lang = t("htmlLang");
  document.querySelectorAll("[data-i18n]").forEach(node => { node.textContent = t(node.dataset.i18n); });
  document.querySelectorAll("[data-i18n-title]").forEach(node => { node.title = t(node.dataset.i18nTitle); });
  document.querySelectorAll("[data-i18n-label]").forEach(node => { node.setAttribute("aria-label", t(node.dataset.i18nLabel)); });
  const toggle = document.getElementById("language-toggle");
  toggle.textContent = t("toggle");
  toggle.setAttribute("aria-label", t("toggleLabel"));
  dialog.setAttribute("aria-label", t("lightbox"));
  document.getElementById("close-lightbox").setAttribute("aria-label", t("closeLabel"));
  document.getElementById("page-title").textContent = data.skill === "comic" ? t("titleComic") : t("titleCharacter");
  const stats = document.getElementById("page-stats");
  stats.replaceChildren();
  for (const [label, value] of [[t("statSources"), data.groups.length], [t("statFinals"), data.groups.reduce((sum, group) => sum + group.passed, 0)], [t("statCalls"), data.groups.reduce((sum, group) => sum + group.calls, 0)]]) {
    const stat = el("span", "stat"); stat.append(el("strong", "", String(value).padStart(2, "0")), el("span", "", label)); stats.append(stat);
  }
  if (dialog.open) updateLightbox();
}
function renderApp() {
  renderStatic();
  app.replaceChildren();
  app.classList.toggle("single-group", data.groups.length < 2);
  tabList = el("nav", "tabs"); tabList.setAttribute("role", "tablist"); tabList.setAttribute("aria-label", t("tabsLabel"));
  tabList.setAttribute("aria-orientation", "vertical");
  const tabsHeading = el("div", "tabs-heading"), hint = el("span", "shortcut");
  hint.append(el("kbd", "", "["), " ", el("kbd", "", "]"), ` ${t("switchGroups")}`);
  tabsHeading.append(el("span", "", t("tabsHeading", {n: data.groups.length})), hint);
  tabList.append(tabsHeading);
  panel = el("div", "group-panel"); panel.id = "group-panel"; panel.setAttribute("role", "tabpanel");
  tabButtons = data.groups.map((group, index) => {
    const tab = button("", () => selectGroup(index, true));
    tab.className = "tab"; tab.id = `group-tab-${index}`;
    tab.setAttribute("role", "tab"); tab.setAttribute("aria-controls", panel.id);
    const picture = groupThumb(group);
    const label = el("span", "tab-text");
    label.append(el("span", "tab-title", `${pad(index + 1)} · ${group.title}`),
                 el("span", "tab-meta", t("tabMeta", {passed: group.passed, planned: group.planned, calls: group.calls})));
    tab.append(picture ? thumbnail(picture.src, "tab-thumb") : el("span", "tab-thumb", pad(index + 1)), label);
    tab.addEventListener("keydown", event => {
      const step = {ArrowUp: -1, ArrowLeft: -1, ArrowDown: 1, ArrowRight: 1}[event.key];
      if (step === undefined && event.key !== "Home" && event.key !== "End") return;
      event.preventDefault();
      const next = event.key === "Home" ? 0 : event.key === "End" ? data.groups.length - 1 : (index + step + data.groups.length) % data.groups.length;
      selectGroup(next); tabButtons[next].focus();
    });
    tabList.append(tab); return tab;
  });
  app.append(tabList, panel); selectGroup(activeGroup);
}
document.getElementById("language-toggle").onclick = () => {
  language = language === "zh" ? "en" : "zh";
  try { localStorage.setItem("whalechan-gallery-language", language); } catch {}
  renderApp();
};
document.addEventListener("keydown", event => {
  if (dialog.open || event.metaKey || event.ctrlKey || event.altKey) return;
  if (/^(INPUT|TEXTAREA|SELECT)$/.test(event.target.tagName) || event.target.isContentEditable) return;
  if (event.key !== "[" && event.key !== "]") return;
  const next = activeGroup + (event.key === "]" ? 1 : -1);
  if (next < 0 || next >= data.groups.length) return;
  event.preventDefault(); selectGroup(next, true); tabButtons[next].focus({preventScroll: true});
});
renderApp();

// Viewer: fit/zoom/pan the current collection, with an optional source comparison and details panel.
const viewer = {scale: 1, fit: 1, x: 0, y: 0, compare: false, info: window.innerWidth > 1180, hinted: false, drag: null};
function entryTitle(entry) { return entry.title || pictureName(entry.picture); }
function comparisonSources(entry) {
  if (!entry.group || entry.picture.kind === "source" || entry.picture.kind === "reference") return [];
  return entry.group.originals.filter(picture => picture.src);
}
function openLightbox(collection, index, origin) {
  opener = origin; currentPictures = collection; currentIndex = index;
  document.body.style.overflow = "hidden";
  dialog.showModal(); stage.focus({preventScroll: true});
  buildStrip(); updateLightbox();
  const hint = document.getElementById("lightbox-hint");
  hint.classList.toggle("gone", viewer.hinted);
  if (!viewer.hinted) { viewer.hinted = true; setTimeout(() => hint.classList.add("gone"), 3200); }
}
function buildStrip() {
  const strip = document.getElementById("lightbox-strip");
  strip.replaceChildren();
  dialog.classList.toggle("single", currentPictures.length < 2);
  currentPictures.forEach((entry, index) => {
    const node = button("", () => moveTo(index));
    node.title = entryTitle(entry); node.setAttribute("aria-label", entryTitle(entry));
    node.append(thumbnail(entry.picture.src));
    strip.append(node);
  });
}
function updateLightbox() {
  const entry = currentPictures[currentIndex], picture = entry.picture;
  largeImage.classList.add("loading");
  largeImage.onload = () => { fitImage(); largeImage.classList.remove("loading"); };
  largeImage.src = picture.src; largeImage.alt = entryTitle(entry);
  if (largeImage.complete && largeImage.naturalWidth) largeImage.onload();
  document.getElementById("lightbox-title").textContent = entryTitle(entry);
  document.getElementById("image-position").textContent = `${currentIndex + 1} / ${currentPictures.length} · ${picture.width} × ${picture.height}`;
  document.getElementById("previous").disabled = currentIndex === 0;
  document.getElementById("next").disabled = currentIndex === currentPictures.length - 1;
  const sources = comparisonSources(entry), compare = document.getElementById("compare-toggle");
  compare.disabled = !sources.length;
  compare.setAttribute("aria-pressed", String(viewer.compare && sources.length > 0));
  viewerMain.classList.toggle("compare", viewer.compare && sources.length > 0);
  const pane = document.getElementById("lightbox-compare");
  pane.replaceChildren(el("p", "section-label", t("sourceInput")), ...sources.map(source => thumbnail(source.src)));
  viewerMain.classList.toggle("info", viewer.info);
  document.getElementById("info-toggle").setAttribute("aria-expanded", String(viewer.info));
  info.replaceChildren(entry.detailFactory ? entry.detailFactory() : el("p", "note", t("inputOrReference")));
  [...document.getElementById("lightbox-strip").children].forEach((node, index) => {
    node.classList.toggle("active", index === currentIndex);
    if (index === currentIndex) node.scrollIntoView({block: "nearest", inline: "nearest"});
  });
  for (const index of [currentIndex - 1, currentIndex + 1]) if (currentPictures[index]) new Image().src = currentPictures[index].picture.src;
}
function moveTo(index) {
  if (index >= 0 && index < currentPictures.length && index !== currentIndex) { currentIndex = index; updateLightbox(); }
}
function stageSize() { return [stage.clientWidth, stage.clientHeight]; }
function isZoomed() { return viewer.scale > viewer.fit * 1.001; }
function applyZoom(animate = false) {
  stage.classList.toggle("animate", animate);
  largeImage.style.width = `${largeImage.naturalWidth}px`; largeImage.style.height = `${largeImage.naturalHeight}px`;
  largeImage.style.transform = `translate(${viewer.x}px, ${viewer.y}px) scale(${viewer.scale})`;
  stage.classList.toggle("zoomed", isZoomed());
  document.getElementById("size-toggle").textContent = isZoomed()
    ? `${Math.round(viewer.scale * 100)}%` : `${t("fit")} ${Math.round(viewer.fit * 100)}%`;
}
function clampPan() {
  const [width, height] = stageSize();
  const imageWidth = largeImage.naturalWidth * viewer.scale, imageHeight = largeImage.naturalHeight * viewer.scale;
  viewer.x = imageWidth <= width ? (width - imageWidth) / 2 : Math.min(0, Math.max(width - imageWidth, viewer.x));
  viewer.y = imageHeight <= height ? (height - imageHeight) / 2 : Math.min(0, Math.max(height - imageHeight, viewer.y));
}
function fitImage(animate = false) {
  if (!largeImage.naturalWidth) return;
  const [width, height] = stageSize();
  const margin = width < 600 ? 16 : 64;
  viewer.fit = Math.max(0.01, Math.min((width - margin) / largeImage.naturalWidth, (height - margin) / largeImage.naturalHeight, 2));
  viewer.scale = viewer.fit; clampPan(); applyZoom(animate);
}
function zoomTo(scale, x, y, animate = false) {
  if (!largeImage.naturalWidth) return;
  const [width, height] = stageSize();
  x ??= width / 2; y ??= height / 2;
  scale = Math.min(Math.max(scale, viewer.fit), 8);
  viewer.x = x - (x - viewer.x) * scale / viewer.scale; viewer.y = y - (y - viewer.y) * scale / viewer.scale;
  viewer.scale = scale; clampPan(); applyZoom(animate);
}
function toggleZoom(x, y) {
  if (isZoomed()) fitImage(true);
  else zoomTo(viewer.fit >= 1 ? viewer.fit * 2 : 1, x, y, true);
}
function stagePoint(event) { const rect = stage.getBoundingClientRect(); return [event.clientX - rect.left, event.clientY - rect.top]; }
stage.addEventListener("wheel", event => {
  event.preventDefault();
  zoomTo(viewer.scale * Math.exp(-event.deltaY * (event.ctrlKey ? 0.01 : 0.0015)), ...stagePoint(event));
}, {passive: false});
stage.addEventListener("pointerdown", event => {
  if (event.button !== 0 || event.target.closest(".lb-arrow")) return;
  viewer.drag = {x: event.clientX, y: event.clientY, panX: viewer.x, panY: viewer.y, moved: false, onImage: event.target === largeImage};
  stage.setPointerCapture(event.pointerId);
});
stage.addEventListener("pointermove", event => {
  const drag = viewer.drag;
  if (!drag) return;
  const dx = event.clientX - drag.x, dy = event.clientY - drag.y;
  if (!drag.moved && Math.hypot(dx, dy) > 4) { drag.moved = true; stage.classList.add("dragging"); }
  if (drag.moved && isZoomed()) { viewer.x = drag.panX + dx; viewer.y = drag.panY + dy; clampPan(); applyZoom(); }
});
stage.addEventListener("pointerup", event => {
  const drag = viewer.drag;
  if (!drag) return;
  viewer.drag = null; stage.classList.remove("dragging");
  if (drag.moved) return;
  if (drag.onImage) toggleZoom(...stagePoint(event));
  else if (!isZoomed()) dialog.close();
});
stage.addEventListener("pointercancel", () => { viewer.drag = null; stage.classList.remove("dragging"); });
window.addEventListener("resize", () => {
  if (!dialog.open) return;
  if (isZoomed()) { clampPan(); applyZoom(); } else fitImage();
});
document.getElementById("previous").onclick = () => moveTo(currentIndex - 1);
document.getElementById("next").onclick = () => moveTo(currentIndex + 1);
document.getElementById("close-lightbox").onclick = () => dialog.close();
document.getElementById("zoom-in").onclick = () => zoomTo(viewer.scale * 1.4, undefined, undefined, true);
document.getElementById("zoom-out").onclick = () => zoomTo(viewer.scale / 1.4, undefined, undefined, true);
document.getElementById("size-toggle").onclick = () => toggleZoom();
document.getElementById("compare-toggle").onclick = () => { viewer.compare = !viewer.compare; updateLightbox(); };
document.getElementById("info-toggle").onclick = () => { viewer.info = !viewer.info; updateLightbox(); };
dialog.addEventListener("close", () => { document.body.style.overflow = ""; opener?.focus(); });
dialog.addEventListener("keydown", event => {
  if (event.target.tagName === "TEXTAREA" || event.metaKey || event.ctrlKey || event.altKey) return;
  const actions = {
    ArrowLeft: () => moveTo(currentIndex - 1), ArrowRight: () => moveTo(currentIndex + 1),
    Home: () => moveTo(0), End: () => moveTo(currentPictures.length - 1),
    "+": () => zoomTo(viewer.scale * 1.4, undefined, undefined, true), "=": () => zoomTo(viewer.scale * 1.4, undefined, undefined, true),
    "-": () => zoomTo(viewer.scale / 1.4, undefined, undefined, true),
    "0": () => fitImage(true), "1": () => zoomTo(1, undefined, undefined, true), z: () => toggleZoom(),
    s: () => document.getElementById("compare-toggle").disabled || document.getElementById("compare-toggle").click(),
    i: () => document.getElementById("info-toggle").click(),
  };
  const action = actions[event.key];
  if (action) { event.preventDefault(); action(); }
});
