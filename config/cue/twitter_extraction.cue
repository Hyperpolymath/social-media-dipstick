-- CUE configuration for Twitter/X policy extraction
-- Provides schema validation and extraction rules

package twitter

import "time"

// Platform configuration
#Platform: {
	name: "twitter"
	displayName: "X (Twitter)"
	enabled: true
	apiEnabled: true
}

// Extraction selectors
#Selectors: {
	// Primary content selectors (in order of preference)
	main: "main"
	article: "article"
	content: ".r-1h0z5md"  // Twitter main content class
	policyText: ".css-901oao"  // Twitter text class

	// Fallback selectors
	fallback: [
		"[role='main']",
		".css-1dbjc4n",
		"body"
	]
}

// Content validation schema
#PolicyContent: {
	url: string
	title?: string
	sections: [...#Section]
	lastModified: time.Time
	checksum: string
}

#Section: {
	heading: string
	content: string
	subsections?: [...#Section]
}

// Extraction rules
#ExtractionRules: {
	// Ignore elements
	ignore: [
		"header",
		"nav",
		"footer",
		".cookie-banner",
		"[aria-hidden='true']"
	]

	// Key terms to extract
	keyTerms: [
		"journalist",
		"reporter",
		"news",
		"media",
		"content creator",
		"publication",
		"copyright",
		"defamation",
		"privacy",
		"harassment",
		"misinformation"
	]

	// Section markers
	sectionMarkers: {
		h1: "major_section"
		h2: "section"
		h3: "subsection"
		h4: "subsubsection"
	}

	// Content filters
	minWordCount: 50
	maxWordCount: 1000000
	stripHTML: true
	normalizeWhitespace: true
}

// Change detection
#ChangeDetection: {
	algorithm: "sha256"
	compareLevel: "section"  // Can be: document, section, paragraph
	significantChangeThreshold: 0.15  // 15% content change

	// Track specific changes
	trackChanges: {
		addedSections: true
		removedSections: true
		modifiedSections: true
		reorderedSections: true
	}
}

// Impact assessment
#ImpactAssessment: {
	// High impact indicators
	highImpact: [
		"suspension",
		"ban",
		"removal",
		"must not",
		"prohibited",
		"violation",
		"consequences",
		"terminate",
		"permanent"
	]

	// Journalist-specific indicators
	journalistImpact: [
		"news organization",
		"press",
		"editorial",
		"source protection",
		"whistleblower",
		"public interest",
		"investigation"
	]

	// Legal terminology
	legalTerms: [
		"liability",
		"indemnify",
		"damages",
		"lawsuit",
		"legal action",
		"court order",
		"subpoena"
	]
}

// Target URLs for extraction
#TargetURLs: {
	termsOfService: "https://twitter.com/en/tos"
	privacyPolicy: "https://twitter.com/en/privacy"
	communityGuidelines: "https://help.twitter.com/en/rules-and-policies/twitter-rules"
	copyrightPolicy: "https://help.twitter.com/en/rules-and-policies/copyright-policy"
	hatefulConduct: "https://help.twitter.com/en/rules-and-policies/hateful-conduct-policy"
}

// Scraping configuration
#ScrapingConfig: {
	requestTimeout: 30  // seconds
	retryAttempts: 3
	retryDelay: 5  // seconds
	rateLimitPerHour: 100
	respectRobotsTxt: true

	// Headers
	headers: {
		"User-Agent": "NUJ Social Media Monitor/1.0"
		"Accept": "text/html,application/xhtml+xml"
		"Accept-Language": "en-US,en;q=0.9"
	}
}

// Validation constraints
#Validation: {
	// Ensure content meets minimum requirements
	minContentLength: 500
	maxContentLength: 5000000

	// Required sections (warn if missing)
	requiredSections: [
		"Terms of Service",
		"Privacy",
		"User Conduct"
	]

	// Validate structure
	validateStructure: true
	requireHeadings: true
	requireLastModified: false
}

// Export configuration
config: {
	platform: #Platform
	selectors: #Selectors
	extractionRules: #ExtractionRules
	changeDetection: #ChangeDetection
	impactAssessment: #ImpactAssessment
	targetURLs: #TargetURLs
	scrapingConfig: #ScrapingConfig
	validation: #Validation
}
