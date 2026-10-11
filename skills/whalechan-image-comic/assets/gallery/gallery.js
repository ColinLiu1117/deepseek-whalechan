"use strict";
const data = JSON.parse(document.getElementById("gallery-data").textContent);
const app = document.getElementById("app");
const dialog = document.getElementById("lightbox");
const largeImage = document.getElementById("large-image");
const stage = document.getElementById("image-stage");
const info = document.getElementById("lightbox-info");
const STRINGS = {
  zh: {
    htmlLang: "zh-CN", toggle: "EN", toggleLabel: "Switch to English",
    masthead: "CREATIVE ARCHIVE / 创作图册", footer: "Whale-chan · 每个灵感，都有迹可循。",
    lightbox: "图片预览", originalSize: "原始尺寸", fitWindow: "适应窗口", imageDetails: "图片详情",
    close: "关闭 ×", closeLabel: "关闭预览", previous: "← 上一张", next: "下一张 →",
    notRecorded: "未记录",
    roles: {candidate: "整图候选", component: "分格组件", composite: "本地合成"},
    refRoles: {identity: "角色身份", style: "画风", proportion: "比例", typography: "文字样式", composition: "构图", costume: "服装", background: "背景", pose_action: "动作"},
    pictures: {candidate: "{label} 候选", source: "输入原图 {label}", reference: "{label}", final: "{label}"},
    reference: "参考图",
    records: {visual_qa: "验收", automatic_qa: "自动验收", prompt: "提示词"},
    warnings: {image_missing: "{subject}：图片文件缺失", record_missing: "{subject} {record}：记录缺失",
               final_ambiguous: "{subject}：多个候选与成品哈希相同，无法唯一确定提示词；请查看生成过程",
               final_unrecorded: "{subject}：成品来源记录缺失"},
    prompt: "实际生图提示词", copyPrompt: "复制提示词", copied: "已复制", selectToCopy: "已选中，请按 ⌘C / Ctrl+C 复制",
    originUnknown: "成品来源未能唯一确认，请查看生成过程。",
    compositeNote: "由分格图片本地合成，不增加产图次数。",
    panelPart: "分格 {id}", panelMissing: "分格来源未记录", recordedAt: "记录时间：{date}",
    collectionQA: "集合审阅与返工记录", minorIssues: "已接受的轻微瑕疵", outcomes: "任务状态与计时",
    qa: "验收记录", qaLine: "自动检查：{automatic} · 视觉检查：{visual}", failUnknown: "失败原因未记录", retry: "修正建议：{retry}",
    imageMissing: "图片文件缺失", noFinal: "尚无通过验收的成品", enlarge: "放大 {label}",
    passed: "已通过", failed: "未通过", notProduced: "未产出", calls: "产图 {n} 次",
    tier: "档位 {tier}", tierContrast: "档位 {tier}（{axes}→{lowered}）", intensity: "强度 {intensity}", axisJoin: "、",
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
    startingPoint: "THE STARTING POINT / 创作起点",
    groupStats: "{passed} / {planned} 张已通过 · 产图 {calls} 次 · {errors} 次接口错误 · {date}",
    request: "用户原始要求", noRequest: "用户原始文字要求未记录；输入素材见下方。",
    analysis: "素材转述 · 非用户原话", references: "角色与视觉参考图 · {n} 张", recordNotes: "记录提示 · {n}",
    allImages: "全部图片 · {n}", proposalsWorks: "方案与作品 · {n}", grid: "▦ 网格", list: "☰ 列表",
    notGenerated: "未生成", proposalPassed: "{passed} / {planned} 张已通过",
    titleComic: "鲸鱼娘 · 漫画图册", titleCharacter: "鲸鱼娘 · 角色图册", tagline: "从一份素材，到一个灵感，再到一张作品。",
    statSources: "素材 / 主题", statFinals: "交付成品", statCalls: "产图次数",
    tabsLabel: "素材组或创作主题", inputOrReference: "输入素材或视觉参考图",
  },
  en: {
    htmlLang: "en", toggle: "中文", toggleLabel: "切换到中文",
    masthead: "CREATIVE ARCHIVE", footer: "Whale-chan · Every idea leaves a trail.",
    lightbox: "Image preview", originalSize: "Original size", fitWindow: "Fit window", imageDetails: "Image details",
    close: "Close ×", closeLabel: "Close preview", previous: "← Previous", next: "Next →",
    notRecorded: "Not recorded",
    roles: {candidate: "Full-canvas candidate", component: "Panel component", composite: "Local composite"},
    refRoles: {identity: "Identity", style: "Style", proportion: "Proportion", typography: "Typography", composition: "Composition", costume: "Costume", background: "Background", pose_action: "Pose & action"},
    pictures: {candidate: "{label} candidate", source: "Input image {label}", reference: "{label}", final: "{label}"},
    reference: "Reference",
    records: {visual_qa: "visual QA", automatic_qa: "automatic QA", prompt: "prompt"},
    warnings: {image_missing: "{subject}: image file missing", record_missing: "{subject} {record}: record missing",
               final_ambiguous: "{subject}: several candidates match the final's hash, so its prompt cannot be identified; see the generation history",
               final_unrecorded: "{subject}: the final's source record is missing"},
    prompt: "Prompt sent to the provider", copyPrompt: "Copy prompt", copied: "Copied", selectToCopy: "Selected — press ⌘C / Ctrl+C to copy",
    originUnknown: "The final's source attempt could not be identified uniquely; see the generation history.",
    compositeNote: "Composed locally from panel images; no extra image-producing call.",
    panelPart: "Panel {id}", panelMissing: "Panel source not recorded", recordedAt: "Recorded: {date}",
    qa: "QA record", qaLine: "Automatic: {automatic} · Visual: {visual}", failUnknown: "Failure reason not recorded", retry: "Suggested fix: {retry}",
    imageMissing: "Image file missing", noFinal: "No passing final yet", enlarge: "Enlarge {label}",
    passed: "Passed", failed: "Failed", notProduced: "Not produced", calls: "{n} image call(s)",
    tier: "Tier {tier}", tierContrast: "Tier {tier} ({axes}→{lowered})", intensity: "Intensity {intensity}", axisJoin: ", ",
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
    startingPoint: "THE STARTING POINT",
    groupStats: "{passed} / {planned} passed · {calls} image call(s) · {errors} provider error(s) · {date}",
    request: "Original request", noRequest: "No written request was recorded; see the input material below.",
    collectionQA: "Collection reviews and repairs", minorIssues: "Accepted minor issues", outcomes: "Task outcomes and timing",
    analysis: "Source transcription · not the user's words", references: "Character and visual references · {n}", recordNotes: "Record notes · {n}",
    allImages: "All images · {n}", proposalsWorks: "Proposals and works · {n}", grid: "▦ Grid", list: "☰ List",
    notGenerated: "Not generated", proposalPassed: "{passed} / {planned} passed",
    titleComic: "Whale-chan · Comic Gallery", titleCharacter: "Whale-chan · Character Gallery", tagline: "From one source, to one idea, to one finished piece.",
    statSources: "Sources / themes", statFinals: "Finals delivered", statCalls: "Image calls",
    tabsLabel: "Source groups or themes", inputOrReference: "Input material or visual reference",
  },
};
function storedLanguage() {
  try { return localStorage.getItem("whalechan-gallery-language"); } catch { return null; }
}
let language = [storedLanguage(), data.language].find(value => value in STRINGS) || "zh";
let activeGroup = 0, view = "grid", currentPictures = [], currentIndex = 0, opener;
const comicFilters = new Map();
function t(key, values = {}) {
  return String(STRINGS[language][key]).replace(/\{(\w+)\}/g, (match, name) => name in values ? values[name] : match);
}
function format(template, values) { return template.replace(/\{(\w+)\}/g, (match, name) => name in values ? values[name] : match); }
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
  if (tier.intensity) return t("intensity", {intensity: tier.intensity});
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
function attemptInfo(attempt, all = []) {
  const box = el("div");
  if (!attempt) { box.append(el("p", "muted", t("originUnknown"))); return box; }
  const meta = el("div", "meta");
  meta.append(badge(roleName(attempt.role)), badge(attempt.verdict || t("notRecorded"), attempt.verdict === "PASS" ? "good" : "warn"));
  box.append(meta);
  if (attempt.role === "composite") {
    box.append(el("p", "note", t("compositeNote")));
    for (const id of attempt.sources) {
      const source = all.find(item => item.id === id);
      const part = details(t("panelPart", {id}));
      if (source) part.append(attemptInfo(source));
      else part.append(el("p", "muted", t("panelMissing")));
      box.append(part);
    }
  } else {
    box.append(el("p", "note", `${text(attempt.provider)} / ${text(attempt.model)}`), promptBlock(attempt.prompt));
  }
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
function imageButton(picture, collection, detailFactory) {
  if (!picture?.src) return el("div", "missing", picture ? t("imageMissing") : t("noFinal"));
  const entry = {picture, detailFactory};
  collection.push(entry);
  const node = button("", () => {
    opener = node;
    currentPictures = collection;
    currentIndex = collection.indexOf(entry);
    updateLightbox();
    dialog.showModal();
    document.body.style.overflow = "hidden";
    document.getElementById("close-lightbox").focus();
  });
  node.className = "picture";
  node.setAttribute("aria-label", t("enlarge", {label: pictureName(picture)}));
  const img = el("img");
  img.src = picture.src; img.alt = pictureName(picture); img.loading = "lazy";
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
  article.append(imageButton(image.final, collection, () => attemptInfo(image.origin, image.attempts)));
  const body = el("div", "card-content");
  body.append(el("h3", "", image.name));
  const meta = el("div", "meta");
  const delivered = image.status === "passed";
  meta.append(badge(delivered ? t("passed") : image.calls ? t("failed") : t("notProduced"), delivered ? "good" : "warn"), badge(t("calls", {n: image.calls})));
  if (image.tier) meta.append(badge(tierText(image.tier)));
  if (image.final?.width) meta.append(badge(`${image.final.width} × ${image.final.height}`));
  body.append(meta);
  if (image.note) body.append(el("p", "note", image.note));
  if (delivered) body.append(attemptInfo(image.origin, image.attempts));
  const history = details(t("history", {calls: image.calls, errors: image.errors.length}));
  const candidates = [];
  image.attempts.forEach(attempt => {
    const section = el("div", "attempt");
    section.append(el("p", "note", `${attempt.id} · ${roleName(attempt.role)}`));
    section.append(imageButton(attempt.picture, candidates, () => attemptInfo(attempt, image.attempts)), attemptInfo(attempt, image.attempts));
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
  if (item.note) box.append(el("p", "note", item.note));
  if (item.matches_final && !item.is_final) {
    box.append(el("p", "note", t("sameAsFinal")));
  }
  if (item.origin_ambiguous) box.append(el("p", "note", t("finalOriginAmbiguous")));
  box.append(attemptInfo(item.attempt, item.attempts));
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
  article.append(imageButton(item.picture, collection, () => galleryImageInfo(item)));
  const body = el("div", "card-content"), meta = el("div", "meta");
  body.append(el("h3", "", item.proposal_title));
  const verdict = item.attempt?.verdict;
  meta.append(badge(verdict === "PASS" ? t("verdictPass") : verdict === "FAIL" ? t("verdictFail") : t("verdictNone"),
                    verdict === "PASS" ? "good" : "warn"));
  if (item.is_final) meta.append(badge(t("final"), "good"));
  else if (item.matches_final) meta.append(badge(t("finalTwin"), "warn"));
  if (item.attempt) meta.append(badge(item.attempt.id), badge(roleName(item.attempt.role)));
  if (item.picture.width) meta.append(badge(`${item.picture.width} × ${item.picture.height}`));
  body.append(meta);
  const more = details(t("imageDetails"));
  more.append(galleryImageInfo(item)); body.append(more);
  if (item.is_final && showHistory) body.append(button(t("viewHistory"), () => showHistory(item.image_id)));
  article.append(body);
  return article;
}
function comicCollections(group) {
  const contexts = new Map();
  group.proposals.forEach(proposal => proposal.images.forEach(image => contexts.set(image.id, {proposal, image})));
  function contextualize(entry) {
    const {proposal, image} = contexts.get(entry.image_id);
    return {...entry, image_name: image.name, proposal_title: proposal.title,
                  scene: proposal.scene, detail: proposal.detail, note: image.note,
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
function renderComicImages(group, panel, heading) {
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
    browser.append(filters);
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
      browser.scrollIntoView({block: "start"});
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
  group.proposals.forEach(proposal => {
    const summary = details(proposal.title);
    summary.append(el("p", "note", proposal.selected ? t("selectedProposal") : t("unselectedProposal")),
                   el("p", "", proposal.scene), el("p", "muted", proposal.detail));
    proposal.images.forEach(image => {
      summary.append(el("p", "note", t("imageSummary", {name: image.name, calls: image.calls, errors: image.errors.length})));
      image.errors.forEach(error => summary.append(el("p", "muted", `${text(error.category)} · ${text(error.details)}`)));
      image.attempts.filter(attempt => !attempt.picture?.src).forEach(attempt => {
        summary.append(el("p", "muted", t("attemptMissing", {id: attempt.id})), attemptInfo(attempt, image.attempts));
      });
    });
    records.append(summary);
  });
  panel.append(records);
}
function renderGroup(group, panel) {
  panel.replaceChildren();
  const source = el("section", "source");
  source.append(el("div", "section-label", t("startingPoint")), el("h2", "", group.title));
  source.append(el("p", "note", t("groupStats", {passed: group.passed, planned: group.planned, calls: group.calls, errors: group.errors, date: date(group.date)})));
  if (group.request) {
    source.append(el("p", "section-label", t("request")), el("p", "source-text", group.request));
  } else source.append(el("p", "note", t("noRequest")));
  if (group.originals.length) source.append(sourceStrip(group.originals));
  if (group.analysis) {
    const analysis = details(t("analysis"));
    analysis.append(el("p", "source-text", group.analysis)); source.append(analysis);
  }
  if (group.references.length) {
    const refs = details(t("references", {n: group.references.length}));
    refs.append(sourceStrip(group.references)); source.append(refs);
  }
  if (group.warnings.length) {
    const warnings = details(t("recordNotes", {n: group.warnings.length}));
    warnings.className = "warnings";
    group.warnings.forEach(warning => warnings.append(el("p", "", warningText(warning))));
    source.append(warnings);
  }
  if (group.collection_reviews?.length) {
    const collection = details(t("collectionQA"));
    group.collection_reviews.forEach(item => {
      collection.append(sourceStrip([item.picture]));
      collection.append(el("pre", "source-text", JSON.stringify(item.review, null, 2)));
    });
    source.append(collection);
  }
  if (group.stage_events?.length) {
    const outcomes = details(t("outcomes"));
    outcomes.append(el("pre", "source-text", JSON.stringify({tasks: group.task_outcomes, events: group.stage_events}, null, 2)));
    source.append(outcomes);
  }
  panel.append(source);
  const toolbar = el("div", "toolbar");
  const heading = el("h2", "", data.skill === "comic"
    ? t("allImages", {n: group.gallery_images.length}) : t("proposalsWorks", {n: group.proposals.length}));
  heading.setAttribute("aria-live", "polite"); toolbar.append(heading);
  const controls = el("div", "controls");
  const modes = [];
  for (const [mode, label] of [["grid", t("grid")], ["list", t("list")]]) {
    const control = button(label, () => {
      view = mode; panel.classList.toggle("list", view === "list");
      modes.forEach(([key, node]) => node.setAttribute("aria-pressed", String(key === view)));
    });
    control.setAttribute("aria-pressed", String(view === mode));
    modes.push([mode, control]); controls.append(control);
  }
  toolbar.append(controls); panel.append(toolbar);
  panel.classList.toggle("list", view === "list");
  if (data.skill === "comic") { renderComicImages(group, panel, heading); return; }
  group.proposals.forEach(proposal => {
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
}
let tabButtons = [], panel;
function selectGroup(index) {
  activeGroup = index;
  tabButtons.forEach((tab, i) => { tab.setAttribute("aria-selected", String(i === index)); tab.tabIndex = i === index ? 0 : -1; });
  panel.setAttribute("aria-labelledby", tabButtons[index].id);
  renderGroup(data.groups[index], panel);
}
function renderStatic() {
  document.documentElement.lang = t("htmlLang");
  document.querySelectorAll("[data-i18n]").forEach(node => { node.textContent = t(node.dataset.i18n); });
  const toggle = document.getElementById("language-toggle");
  toggle.textContent = t("toggle");
  toggle.setAttribute("aria-label", t("toggleLabel"));
  dialog.setAttribute("aria-label", t("lightbox"));
  document.getElementById("close-lightbox").setAttribute("aria-label", t("closeLabel"));
  document.getElementById("size-toggle").textContent = stage.classList.contains("original") ? t("fitWindow") : t("originalSize");
}
function renderApp() {
  renderStatic();
  app.replaceChildren();
  const hero = el("section", "hero"), introduction = el("div");
  introduction.append(el("div", "eyebrow", "A COLLECTION OF LITTLE IDEAS"), el("h1", "", data.skill === "comic" ? t("titleComic") : t("titleCharacter")), el("p", "", t("tagline")));
  const stats = el("div", "stats");
  for (const [label, value] of [[t("statSources"), data.groups.length], [t("statFinals"), data.groups.reduce((sum, group) => sum + group.passed, 0)], [t("statCalls"), data.groups.reduce((sum, group) => sum + group.calls, 0)]]) {
    const stat = el("div", "stat"); stat.append(el("strong", "", String(value).padStart(2, "0")), el("span", "", label)); stats.append(stat);
  }
  hero.append(introduction, stats); app.append(hero);
  const tabs = el("nav", "tabs"); tabs.setAttribute("role", "tablist"); tabs.setAttribute("aria-label", t("tabsLabel"));
  panel = el("div"); panel.id = "group-panel"; panel.setAttribute("role", "tabpanel");
  tabButtons = data.groups.map((group, index) => {
    const tab = button(`${String(index + 1).padStart(2,"0")} / ${group.title}`, () => selectGroup(index));
    tab.id = `group-tab-${index}`; tab.setAttribute("role", "tab"); tab.setAttribute("aria-controls", panel.id);
    tab.addEventListener("keydown", event => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const next = event.key === "Home" ? 0 : event.key === "End" ? data.groups.length - 1 : (index + (event.key === "ArrowRight" ? 1 : -1) + data.groups.length) % data.groups.length;
      selectGroup(next); tabButtons[next].focus();
    });
    tabs.append(tab); return tab;
  });
  app.append(tabs, panel); selectGroup(activeGroup);
}
document.getElementById("language-toggle").onclick = () => {
  language = language === "zh" ? "en" : "zh";
  try { localStorage.setItem("whalechan-gallery-language", language); } catch {}
  renderApp();
};
renderApp();
function updateLightbox() {
  const entry = currentPictures[currentIndex];
  largeImage.src = entry.picture.src; largeImage.alt = pictureName(entry.picture);
  document.getElementById("lightbox-title").textContent = pictureName(entry.picture);
  document.getElementById("image-position").textContent = `${currentIndex + 1} / ${currentPictures.length} · ${entry.picture.width} × ${entry.picture.height}`;
  document.getElementById("previous").disabled = currentIndex === 0;
  document.getElementById("next").disabled = currentIndex === currentPictures.length - 1;
  stage.classList.remove("original"); stage.scrollTop = 0; stage.scrollLeft = 0;
  document.getElementById("size-toggle").textContent = t("originalSize");
  info.replaceChildren(entry.detailFactory ? entry.detailFactory() : el("p", "note", t("inputOrReference")));
}
function move(delta) {
  const next = currentIndex + delta;
  if (next >= 0 && next < currentPictures.length) { currentIndex = next; updateLightbox(); }
}
document.getElementById("previous").onclick = () => move(-1);
document.getElementById("next").onclick = () => move(1);
document.getElementById("close-lightbox").onclick = () => dialog.close();
document.getElementById("size-toggle").onclick = event => {
  stage.classList.toggle("original");
  event.currentTarget.textContent = stage.classList.contains("original") ? t("fitWindow") : t("originalSize");
};
document.getElementById("info-toggle").onclick = event => {
  info.hidden = !info.hidden; event.currentTarget.setAttribute("aria-expanded", String(!info.hidden));
};
dialog.addEventListener("click", event => { if (event.target === dialog) dialog.close(); });
dialog.addEventListener("close", () => { document.body.style.overflow = ""; opener?.focus(); });
dialog.addEventListener("keydown", event => {
  if (event.target.tagName === "TEXTAREA") return;
  if (event.key === "ArrowLeft" || event.key === "ArrowRight") { event.preventDefault(); move(event.key === "ArrowLeft" ? -1 : 1); }
});
