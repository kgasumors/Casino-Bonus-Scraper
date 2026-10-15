<script setup>
    import data from '../data/bonuses.json'

    const casinos = data.casinos
    const scrapedAt = new Date(data.scraped_at).toLocaleDateString('en-ZA', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    })
    const sourceHost = new URL(data.source_url).hostname
</script>

<template>
  <section class="mx-auto w-full max-w-4xl px-4 py-10 sm:py-14">
    <header class="mb-8">
      <p class="text-xs font-semibold uppercase tracking-widest text-emerald-600">
        Casino Bonus Scraper
      </p>
      <h1 class="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
        Casino bonuses compared
      </h1>
      <p class="mt-3 text-sm text-slate-600 sm:text-base">
        Three South African casino welcome offers, with the wagering requirement.
      </p>
    </header>

    <!-- Desktop / tablet: table -->
    <div class="hidden overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm md:block">
      <table class="w-full text-left text-sm">
        <thead class="bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
          <tr>
            <th scope="col" class="px-6 py-4 font-semibold">Casino</th>
            <th scope="col" class="px-6 py-4 font-semibold">Bonus</th>
            <th scope="col" class="px-6 py-4 font-semibold">Wagering</th>
            <th scope="col" class="px-6 py-4 font-semibold">Min. deposit</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr
            v-for="casino in casinos"
            :key="casino.casino_name"
            class="transition hover:bg-emerald-50/40"
          >
            <th scope="row" class="px-6 py-5 text-base font-semibold text-slate-900">
              {{ casino.casino_name }}
            </th>
            <td class="px-6 py-5 text-slate-700">{{ casino.bonus_offer ?? '—' }}</td>
            <td class="px-6 py-5">
              <span
                v-if="casino.wagering_requirement"
                class="inline-block rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800"
              >
                {{ casino.wagering_requirement }}
              </span>
              <span v-else class="text-slate-400">—</span>
            </td>
            <td class="px-6 py-5 font-medium text-slate-900">
              {{ casino.minimum_deposit ?? '—' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Phone: stacked cards for mobile -->
    <ul class="space-y-4 md:hidden">
      <li
        v-for="casino in casinos"
        :key="casino.casino_name"
        class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
      >
        <h2 class="text-lg font-semibold text-slate-900">{{ casino.casino_name }}</h2>
        <p class="mt-2 text-base leading-snug text-slate-700">
          {{ casino.bonus_offer ?? '—' }}
        </p>

        <dl class="mt-4 grid grid-cols-2 gap-3 border-t border-slate-100 pt-4">
          <div>
            <dt class="text-xs font-semibold uppercase tracking-wider text-slate-500">Wagering</dt>
            <dd class="mt-1">
              <span
                v-if="casino.wagering_requirement"
                class="inline-block rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800"
              >
                {{ casino.wagering_requirement }}
              </span>
              <span v-else class="text-slate-400">—</span>
            </dd>
          </div>
          <div>
            <dt class="text-xs font-semibold uppercase tracking-wider text-slate-500">Min. deposit</dt>
            <dd class="mt-1 text-base font-semibold text-slate-900">
              {{ casino.minimum_deposit ?? '—' }}
            </dd>
          </div>
        </dl>
      </li>
    </ul>

    <footer class="mt-8 space-y-2 text-xs text-slate-500">
      <p>
        Data collected from {{ sourceHost }} on {{ scrapedAt }}. Terms change often, so
        confirm them on the casino's own site before you deposit.
      </p>
    </footer>
  </section>
</template>