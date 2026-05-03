<script lang="ts">
	import { onMount } from 'svelte';
	import { fade, fly } from 'svelte/transition';

	let activeSection = $state('introduction');

	const sections = [
		{ id: 'introduction', title: '1. Introduction' },
		{ id: 'acceptance', title: '2. Acceptance of Terms' },
		{ id: 'service', title: '3. Description of Service' },
		{ id: 'conduct', title: '4. User Conduct' },
		{ id: 'intellectual-property', title: '5. Intellectual Property' },
		{ id: 'disclaimer', title: '6. Disclaimer of Warranties' },
		{ id: 'liability', title: '7. Limitation of Liability' },
		{ id: 'indemnification', title: '8. Indemnification' },
		{ id: 'governing-law', title: '9. Governing Law' },
		{ id: 'changes', title: '10. Changes to Terms' }
	];

	function scrollToSection(id: string) {
		const element = document.getElementById(id);
		if (element) {
			element.scrollIntoView({ behavior: 'smooth' });
			activeSection = id;
		}
	}

	onMount(() => {
		const observer = new IntersectionObserver(
			(entries) => {
				entries.forEach((entry) => {
					if (entry.isIntersecting) {
						activeSection = entry.target.id;
					}
				});
			},
			{ threshold: 0.5 }
		);

		sections.forEach((section) => {
			const element = document.getElementById(section.id);
			if (element) observer.observe(element);
		});

		return () => observer.disconnect();
	});
</script>

<svelte:head>
	<title>Terms & Conditions | DevBeast</title>
	<meta name="description" content="Legal Terms and Conditions for using the DevBeast Workspace application." />
</svelte:head>

<div class="flex flex-col h-full overflow-hidden" in:fade={{ duration: 400 }}>
	<!-- Header Area -->
	<header class="mb-10 shrink-0">
		<div class="flex items-center gap-3 mb-2">
			<div class="px-3 py-1 bg-indigo-500/10 border border-indigo-500/20 rounded-full">
				<span class="text-[10px] font-black text-indigo-500 uppercase tracking-[0.2em]">Legal Documentation</span>
			</div>
			<span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Last Updated: May 2026</span>
		</div>
		<h1 class="text-4xl font-black text-slate-900 dark:text-white tracking-tight mb-4">
			Terms & <span class="text-indigo-500 italic">Conditions</span>
		</h1>
		<p class="text-slate-500 dark:text-slate-400 max-w-2xl leading-relaxed">
			Please read these terms and conditions carefully before using the DevBeast Workspace. This document outlines your legal rights and responsibilities.
		</p>
	</header>

	<div class="flex flex-1 gap-12 min-h-0 overflow-hidden pb-10">
		<!-- Sidebar Navigation -->
		<aside class="w-64 shrink-0 hidden lg:block">
			<div class="sticky top-0 space-y-1">
				{#each sections as section}
					<button
						onclick={() => scrollToSection(section.id)}
						class={[
							"w-full text-left px-4 py-3 rounded-xl transition-all duration-300 text-sm font-medium",
							activeSection === section.id
								? "bg-indigo-500 text-white shadow-lg shadow-indigo-500/20 translate-x-1"
								: "text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-900"
						].join(" ")}
					>
						{section.title}
					</button>
				{/each}
			</div>
		</aside>

		<!-- Content Area -->
		<main class="flex-1 overflow-y-auto custom-scrollbar pr-4 -mr-4 space-y-12">
			<section id="introduction" class="scroll-mt-10">
				<h2 class="text-2xl font-bold text-slate-900 dark:text-white mb-4">1. Introduction</h2>
				<div class="prose prose-slate dark:prose-invert max-w-none text-slate-600 dark:text-slate-400 leading-relaxed space-y-4">
					<p>
						Welcome to DevBeast Workspace ("the Application"). These Terms and Conditions govern your use of the Application, which is designed to provide development tools, container management, and related services.
					</p>
					<p>
						By accessing or using the Application, you agree to be bound by these Terms. If you disagree with any part of the terms, you may not access the service.
					</p>
				</div>
			</section>

			<section id="acceptance" class="scroll-mt-10">
				<h2 class="text-2xl font-bold text-slate-900 dark:text-white mb-4">2. Acceptance of Terms</h2>
				<div class="prose prose-slate dark:prose-invert max-w-none text-slate-600 dark:text-slate-400 leading-relaxed space-y-4">
					<p>
						Your access to and use of the Application is conditioned on your acceptance of and compliance with these Terms. These Terms apply to all visitors, users, and others who access or use the Application.
					</p>
				</div>
			</section>

			<section id="service" class="scroll-mt-10">
				<h2 class="text-2xl font-bold text-slate-900 dark:text-white mb-4">3. Description of Service</h2>
				<div class="prose prose-slate dark:prose-invert max-w-none text-slate-600 dark:text-slate-400 leading-relaxed space-y-4">
					<p>
						DevBeast Workspace provides a suite of tools for local development, including but not limited to container orchestration, network monitoring, and database management. We reserve the right to withdraw or amend the service we provide without notice.
					</p>
				</div>
			</section>

			<section id="conduct" class="scroll-mt-10">
				<h2 class="text-2xl font-bold text-slate-900 dark:text-white mb-4">4. User Conduct</h2>
				<div class="prose prose-slate dark:prose-invert max-w-none text-slate-600 dark:text-slate-400 leading-relaxed space-y-4">
					<p>
						You agree not to use the Application for any purpose that is unlawful or prohibited by these Terms. You may not:
					</p>
					<ul class="list-disc pl-5 space-y-2">
						<li>Attempt to gain unauthorized access to any portion or feature of the Application.</li>
						<li>Interfere with or disrupt the operation of the Application.</li>
						<li>Use the Application to distribute malware, spyware, or any other malicious code.</li>
						<li>Use the Application for any illegal or unauthorized purpose.</li>
					</ul>
				</div>
			</section>

			<section id="intellectual-property" class="scroll-mt-10">
				<h2 class="text-2xl font-bold text-slate-900 dark:text-white mb-4">5. Intellectual Property</h2>
				<div class="prose prose-slate dark:prose-invert max-w-none text-slate-600 dark:text-slate-400 leading-relaxed space-y-4">
					<p>
						The Application and its original content, features, and functionality are and will remain the exclusive property of DevBeast and its licensors. The Application is protected by copyright, trademark, and other laws of both the country and foreign countries.
					</p>
				</div>
			</section>

			<section id="disclaimer" class="scroll-mt-10">
				<h2 class="text-2xl font-bold text-slate-900 dark:text-white mb-4">6. Disclaimer of Warranties</h2>
				<div class="bg-amber-500/5 border border-amber-500/20 p-6 rounded-2xl mb-4">
					<p class="text-slate-600 dark:text-slate-300 font-medium leading-relaxed uppercase text-xs tracking-wider mb-2">Notice to User</p>
					<p class="text-slate-600 dark:text-slate-400 italic">
						"YOUR USE OF THE SERVICE IS AT YOUR SOLE RISK. THE SERVICE IS PROVIDED ON AN 'AS IS' AND 'AS AVAILABLE' BASIS. THE SERVICE IS PROVIDED WITHOUT WARRANTIES OF ANY KIND."
					</p>
				</div>
				<div class="prose prose-slate dark:prose-invert max-w-none text-slate-600 dark:text-slate-400 leading-relaxed">
					<p>
						DevBeast does not warrant that: a) the service will function uninterrupted, secure or available at any particular time or location; b) any errors or defects will be corrected; c) the service is free of viruses or other harmful components; or d) the results of using the service will meet your requirements.
					</p>
				</div>
			</section>

			<section id="liability" class="scroll-mt-10">
				<div class="p-8 bg-rose-500/5 border-2 border-rose-500/20 rounded-3xl relative overflow-hidden">
					<div class="absolute top-0 right-0 p-4 opacity-10">
						<svg class="w-24 h-24 text-rose-500" fill="currentColor" viewBox="0 0 24 24">
							<path d="M12 2L1 21h22L12 2zm0 3.99L19.53 19H4.47L12 5.99zM11 16h2v2h-2v-2zm0-7h2v5h-2V9z"/>
						</svg>
					</div>
					<h2 class="text-2xl font-black text-slate-900 dark:text-white mb-4 uppercase tracking-tight">7. Limitation of Liability</h2>
					<div class="prose prose-slate dark:prose-invert max-w-none text-slate-900 dark:text-slate-100 font-bold leading-relaxed space-y-4">
						<p class="text-lg">
							IN NO EVENT SHALL DEVBEAST, NOR ITS DIRECTORS, EMPLOYEES, PARTNERS, AGENTS, SUPPLIERS, OR AFFILIATES, BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL OR PUNITIVE DAMAGES, INCLUDING WITHOUT LIMITATION, LOSS OF PROFITS, DATA, USE, GOODWILL, OR OTHER INTANGIBLE LOSSES, RESULTING FROM:
						</p>
						<ul class="list-disc pl-5 space-y-2 uppercase text-sm">
							<li>YOUR ACCESS TO OR USE OF OR INABILITY TO ACCESS OR USE THE SERVICE;</li>
							<li>ANY CONDUCT OR CONTENT OF ANY THIRD PARTY ON THE SERVICE;</li>
							<li>ANY CONTENT OBTAINED FROM THE SERVICE; AND</li>
							<li>UNAUTHORIZED ACCESS, USE OR ALTERATION OF YOUR TRANSMISSIONS OR CONTENT, WHETHER BASED ON WARRANTY, CONTRACT, TORT (INCLUDING NEGLIGENCE) OR ANY OTHER LEGAL THEORY, WHETHER OR NOT WE HAVE BEEN INFORMED OF THE POSSIBILITY OF SUCH DAMAGE.</li>
						</ul>
					</div>
				</div>
			</section>

			<section id="indemnification" class="scroll-mt-10">
				<h2 class="text-2xl font-bold text-slate-900 dark:text-white mb-4">8. Indemnification</h2>
				<div class="prose prose-slate dark:prose-invert max-w-none text-slate-600 dark:text-slate-400 leading-relaxed space-y-4">
					<p>
						You agree to defend, indemnify and hold harmless DevBeast and its licensee and licensors, and their employees, contractors, agents, officers and directors, from and against any and all claims, damages, obligations, losses, liabilities, costs or debt, and expenses (including but not limited to attorney's fees), resulting from or arising out of a) your use and access of the Service, or b) a breach of these Terms.
					</p>
				</div>
			</section>

			<section id="governing-law" class="scroll-mt-10">
				<h2 class="text-2xl font-bold text-slate-900 dark:text-white mb-4">9. Governing Law</h2>
				<div class="prose prose-slate dark:prose-invert max-w-none text-slate-600 dark:text-slate-400 leading-relaxed space-y-4">
					<p>
						These Terms shall be governed and construed in accordance with the laws of the jurisdiction in which DevBeast operates, without regard to its conflict of law provisions.
					</p>
				</div>
			</section>

			<section id="changes" class="scroll-mt-10">
				<h2 class="text-2xl font-bold text-slate-900 dark:text-white mb-4">10. Changes to Terms</h2>
				<div class="prose prose-slate dark:prose-invert max-w-none text-slate-600 dark:text-slate-400 leading-relaxed space-y-4">
					<p>
						We reserve the right, at our sole discretion, to modify or replace these Terms at any time. If a revision is material we will try to provide at least 30 days notice prior to any new terms taking effect. What constitutes a material change will be determined at our sole discretion.
					</p>
				</div>
			</section>
			
			<div class="pt-10 border-t border-slate-200 dark:border-slate-800">
				<p class="text-sm text-slate-500 text-center">
					If you have any questions about these Terms, please contact us.
				</p>
			</div>
		</main>
	</div>
</div>

<style>
	/* Smooth scrolling for the whole page */
	:global(html) {
		scroll-behavior: smooth;
	}
</style>
