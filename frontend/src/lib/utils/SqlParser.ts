export interface QueryContext {
	aliases: Record<string, string>;
	nearestKeyword: string | null;
	afterDot: string | null;
}

/**
 * A lightweight, error-tolerant SQL parser to extract context from a query string.
 * Focused on identifying table aliases and the current cursor's semantic location.
 */
export function parseQueryContext(sql: string, pos: number): QueryContext {
	const textBefore = sql.slice(0, pos);
	const aliases: Record<string, string> = {};
	
	// 1. Identify Table Aliases
	// Look for: FROM table alias, FROM schema.table alias, JOIN table alias, etc.
	// This regex is intentionally broad to be error-tolerant.
	const tableAliasRegex = /(?:FROM|JOIN)\s+([a-zA-Z0-9_.]+(?:\.[a-zA-Z0-9_.]+)?)(?:\s+AS)?\s+([a-zA-Z0-9_]+)/gi;
	let match;
	while ((match = tableAliasRegex.exec(sql)) !== null) {
		const tableName = match[1];
		const aliasName = match[2];
		
		// Map alias to table name (e.g., "u" -> "public.users")
		// Ensure table name is schema-qualified for consistent lookup
		const qualifiedTable = tableName.includes('.') ? tableName : `public.${tableName}`;
		aliases[aliasName.toLowerCase()] = qualifiedTable;
	}

	// 2. Identify Nearest Preceding Keyword
	const keywords = ['SELECT', 'FROM', 'JOIN', 'WHERE', 'SET', 'GROUP BY', 'ORDER BY', 'INSERT INTO', 'UPDATE', 'DELETE FROM'];
	let nearestKeyword: string | null = null;
	let lastIndex = -1;

	for (const kw of keywords) {
		const index = textBefore.toUpperCase().lastIndexOf(kw);
		if (index > lastIndex) {
			lastIndex = index;
			nearestKeyword = kw;
		}
	}

	// 3. Check for member access (e.g., "u.")
	const afterDotMatch = textBefore.match(/([a-zA-Z0-9_]+)\.$/);
	const afterDot = afterDotMatch ? afterDotMatch[1] : null;

	return {
		aliases,
		nearestKeyword,
		afterDot
	};
}
