import { useEffect, useMemo, useRef } from 'react';

import type { Lesson } from '../components';
import { assetUrl } from './lessonUrls';
import {
  planLessonStartAssets,
  planNextLessonAssets,
  planUpcomingStepAssets,
  shouldPrimeNextLesson,
  type AssetPrefetchPlan,
} from './lessonAssetPlan';

type PrefetchPriority = 'critical' | 'soon' | 'background';
type AssetType = 'image' | 'audio';

type PrefetchTask = {
  key: string;
  url: string;
  type: AssetType;
  priority: PrefetchPriority;
};

type UseAssetPrefetcherOptions = {
  sessionPhase: 'landing' | 'running' | 'complete';
  firstLesson: Lesson | null;
  currentLesson: Lesson | null;
  currentStepId: string | null;
  nextLesson: Lesson | null;
  isAudioPlaying: boolean;
};

const PRIORITIES: PrefetchPriority[] = ['critical', 'soon', 'background'];
const IMAGE_CONCURRENCY = 2;
const AUDIO_CONCURRENCY = 1;
const MAX_BACKGROUND_QUEUE = 8;

class AssetPrefetchQueue {
  private readonly queued = new Set<string>();
  private readonly completed = new Set<string>();
  private readonly inflight = new Set<string>();
  private readonly queue = new Map<PrefetchPriority, PrefetchTask[]>(
    PRIORITIES.map((priority) => [priority, []]),
  );
  private readonly audioCache = new Map<string, HTMLAudioElement>();
  private readonly imageCache = new Map<string, HTMLImageElement>();
  private activeImages = 0;
  private activeAudio = 0;
  private backgroundPaused = false;

  enqueuePlan(plan: AssetPrefetchPlan) {
    this.enqueue(plan.critical, 'critical');
    this.enqueue(plan.soon, 'soon');
    this.enqueue(plan.background, 'background');
  }

  enqueue(urls: string[], priority: PrefetchPriority) {
    const tasks = this.queue.get(priority);
    if (!tasks) {
      return;
    }

    for (const rawUrl of urls) {
      const url = this.normalize(rawUrl);
      if (!url) {
        continue;
      }
      const type = detectAssetType(url);
      const key = `${type}:${url}`;
      if (this.completed.has(key) || this.inflight.has(key) || this.queued.has(key)) {
        continue;
      }
      if (priority === 'background' && tasks.length >= MAX_BACKGROUND_QUEUE) {
        break;
      }
      tasks.push({ key, url, type, priority });
      this.queued.add(key);
    }

    this.schedule();
  }

  setBackgroundPaused(paused: boolean) {
    this.backgroundPaused = paused;
    if (!paused) {
      this.schedule();
    }
  }

  has(url: string): boolean {
    const normalized = this.normalize(url);
    return normalized ? this.completed.has(`audio:${normalized}`) || this.completed.has(`image:${normalized}`) : false;
  }

  getAudioForPlayback(url: string): HTMLAudioElement | null {
    const normalized = this.normalize(url);
    if (!normalized) {
      return null;
    }
    const cached = this.audioCache.get(normalized);
    if (!cached || cached.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
      return null;
    }
    if (!cached.paused) {
      return null;
    }
    cached.currentTime = 0;
    return cached;
  }

  private schedule() {
    while (this.activeImages < IMAGE_CONCURRENCY) {
      const task = this.nextTask('image');
      if (!task) {
        break;
      }
      this.start(task);
    }

    while (this.activeAudio < AUDIO_CONCURRENCY) {
      const task = this.nextTask('audio');
      if (!task) {
        break;
      }
      this.start(task);
    }
  }

  private nextTask(type: AssetType): PrefetchTask | null {
    for (const priority of PRIORITIES) {
      if (priority === 'background' && this.backgroundPaused) {
        continue;
      }
      const tasks = this.queue.get(priority);
      if (!tasks || tasks.length === 0) {
        continue;
      }
      const taskIndex = tasks.findIndex((item) => item.type === type);
      if (taskIndex < 0) {
        continue;
      }
      const [task] = tasks.splice(taskIndex, 1);
      this.queued.delete(task.key);
      return task;
    }
    return null;
  }

  private start(task: PrefetchTask) {
    this.inflight.add(task.key);
    if (task.type === 'image') {
      this.activeImages += 1;
      this.prefetchImage(task)
        .catch(() => undefined)
        .finally(() => {
          this.inflight.delete(task.key);
          this.completed.add(task.key);
          this.activeImages = Math.max(0, this.activeImages - 1);
          this.schedule();
        });
      return;
    }

    this.activeAudio += 1;
    this.prefetchAudio(task)
      .catch(() => undefined)
      .finally(() => {
        this.inflight.delete(task.key);
        this.completed.add(task.key);
        this.activeAudio = Math.max(0, this.activeAudio - 1);
        this.schedule();
      });
  }

  private prefetchImage(task: PrefetchTask): Promise<void> {
    return new Promise((resolve) => {
      const image = new Image();
      image.decoding = 'async';
      image.onload = () => resolve();
      image.onerror = () => resolve();
      image.src = task.url;
      this.imageCache.set(task.url, image);
    });
  }

  private prefetchAudio(task: PrefetchTask): Promise<void> {
    return new Promise((resolve) => {
      const audio = new Audio();
      audio.preload = 'auto';
      audio.oncanplaythrough = () => resolve();
      audio.onerror = () => resolve();
      audio.src = task.url;
      audio.load();
      this.audioCache.set(task.url, audio);
    });
  }

  private normalize(url: string): string | null {
    const trimmed = String(url || '').trim();
    if (!trimmed) {
      return null;
    }
    return assetUrl(trimmed);
  }
}

const prefetchQueue = new AssetPrefetchQueue();

export function useAssetPrefetcher({
  sessionPhase,
  firstLesson,
  currentLesson,
  currentStepId,
  nextLesson,
  isAudioPlaying,
}: UseAssetPrefetcherOptions) {
  const primedNextLessonIdsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    prefetchQueue.setBackgroundPaused(isAudioPlaying);
  }, [isAudioPlaying]);

  const landingPlan = useMemo(() => {
    if (!firstLesson || sessionPhase !== 'landing') {
      return null;
    }
    return planLessonStartAssets(firstLesson);
  }, [firstLesson, sessionPhase]);

  useEffect(() => {
    if (!landingPlan) {
      return;
    }
    prefetchQueue.enqueuePlan(landingPlan);
  }, [landingPlan]);

  const runningPlan = useMemo(() => {
    if (sessionPhase !== 'running' || !currentLesson || !currentStepId) {
      return null;
    }
    return planUpcomingStepAssets(currentLesson, currentStepId);
  }, [sessionPhase, currentLesson, currentStepId]);

  useEffect(() => {
    if (!runningPlan) {
      return;
    }
    prefetchQueue.enqueuePlan(runningPlan);
  }, [runningPlan]);

  useEffect(() => {
    if (sessionPhase !== 'running' || !currentLesson || !currentStepId || !nextLesson) {
      return;
    }
    if (primedNextLessonIdsRef.current.has(nextLesson.id)) {
      return;
    }
    if (!shouldPrimeNextLesson(currentLesson, currentStepId)) {
      return;
    }

    prefetchQueue.enqueuePlan(planNextLessonAssets(nextLesson));
    primedNextLessonIdsRef.current.add(nextLesson.id);
  }, [sessionPhase, currentLesson, currentStepId, nextLesson]);
}

export function getPrefetchedAudioElement(url: string): HTMLAudioElement | null {
  return prefetchQueue.getAudioForPlayback(url);
}

export function prefetchHasAsset(url: string): boolean {
  return prefetchQueue.has(url);
}

function detectAssetType(url: string): AssetType {
  return /\.(png|jpg|jpeg|webp|gif)(\?|$)/i.test(url) ? 'image' : 'audio';
}
