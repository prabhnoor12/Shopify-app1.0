
import React, { useEffect, useState, useMemo } from 'react';

interface ABTestingDashboardProps {
	onTestSelect: (testId: number) => void;
	onNewTest: () => void;
	forceStopLoading: boolean;
}
import './ABTestingDashboard.css';
import { abTestingApi } from '../../../api/abTestingApi';
import { client } from '../../../api/client';

// Helper to build query string for pagination
function buildQuery(base: string, params: Record<string, any>): string {
	const esc = encodeURIComponent;
	const query = Object.keys(params)
		.filter(k => params[k] !== undefined && params[k] !== null)
		.map(k => esc(k) + '=' + esc(params[k]))
		.join('&');
	return query ? `${base}?${query}` : base;
}

type Variant = {
  id: string;
  name: string;
  conversionRate: number;
  users: number;
};

type ABTest = {
  id: string;
  name: string;
  status: 'Running' | 'Completed' | 'Scheduled';
  startDate: string;
  endDate?: string;
  variants: Variant[];
};


const ABTestingDashboard: React.FC<ABTestingDashboardProps> = ({ onTestSelect, onNewTest, forceStopLoading }) => {
	const [tests, setTests] = useState<ABTest[]>([]);
	const [loading, setLoading] = useState<boolean>(true);
						const [error, setError] = useState<string | null>(null);
						const [loadingTimeout, setLoadingTimeout] = useState<boolean>(false);

						// Stop loading if forceStopLoading is true
						useEffect(() => {
							if (forceStopLoading) {
								setLoading(false);
								setLoadingTimeout(false);
							}
						}, [forceStopLoading]);
			// Pagination state
			const [page, setPage] = useState<number>(1);
			const [pageSize] = useState<number>(30); // can be adjusted
			const [hasMore, setHasMore] = useState<boolean>(true);
			const [isFetchingMore, setIsFetchingMore] = useState<boolean>(false);

			useEffect(() => {
				setLoading(true);
				setLoadingTimeout(false);
				setPage(1);
				setHasMore(true);
				const timeout = setTimeout(() => {
					setLoadingTimeout(true);
					setLoading(false);
				}, 5000);

					abTestingApi.getTests &&
					abTestingApi.getTests.length === 0 &&
					client.get &&
					client.get.length > 0;
					client.get(buildQuery('/api/ab-tests', { page: 1, page_size: pageSize }))
						.then((data: ABTest[] | { results: ABTest[], has_more?: boolean }) => {
						let results: ABTest[] = [];
						let more = true;
						if (Array.isArray(data)) {
							results = data;
							more = data.length === pageSize;
						} else if (data && Array.isArray((data as any).results)) {
							results = (data as any).results;
							more = (data as any).has_more !== undefined ? (data as any).has_more : results.length === pageSize;
						}
						setTests(results);
						setHasMore(more);
						setError(null);
						clearTimeout(timeout);
						setLoading(false);
					})
					.catch((err) => {
						setError(err.message || 'Failed to load A/B tests');
						setTests([]);
						setHasMore(false);
						clearTimeout(timeout);
						setLoading(false);
					});

				return () => clearTimeout(timeout);
				// eslint-disable-next-line
			}, [pageSize]);

			// Fetch more for infinite scroll or pagination
			const fetchMore = () => {
				if (!hasMore || isFetchingMore) return;
				setIsFetchingMore(true);
					client.get(buildQuery('/api/ab-tests', { page: page + 1, page_size: pageSize }))
						.then((data: ABTest[] | { results: ABTest[], has_more?: boolean }) => {
						let results: ABTest[] = [];
						let more = true;
						if (Array.isArray(data)) {
							results = data;
							more = data.length === pageSize;
						} else if (data && Array.isArray((data as any).results)) {
							results = (data as any).results;
							more = (data as any).has_more !== undefined ? (data as any).has_more : results.length === pageSize;
						}
						setTests(prev => [...prev, ...results]);
						setPage(prev => prev + 1);
						setHasMore(more);
					})
					.catch(() => setHasMore(false))
					.finally(() => setIsFetchingMore(false));
			};

			// Memoize filtered lists for performance
			const activeTests = useMemo(() => tests.filter(test => test.status === 'Running'), [tests]);

		return (
			<div className="ab-dashboard">
				<h1>A/B Testing Dashboard</h1>
				<button onClick={onNewTest} className="ab-newtest-btn" aria-label="Create new A/B test">New Test</button>

				{loading && <div className="ab-loading">Loading tests...</div>}
				{loadingTimeout && !error && tests.length === 0 && (
					<div className="ab-empty">The backend is empty. No A/B tests found.</div>
				)}
				{error && <div className="ab-error">{error}</div>}

				{!loading && !error && (
					<>
							<section className="ab-summary" aria-label="Active A/B Tests">
								<h2>Active Tests</h2>
								{activeTests.length === 0 ? (
									<div className="ab-empty">No active tests found.</div>
								) : (
									<ul>
										{activeTests.map(test => (
											<li key={test.id}>
												<strong>{test.name}</strong> (Started: {test.startDate})
												<button onClick={() => onTestSelect(Number(test.id))} className="ab-select-btn" aria-label={`Select test ${test.name}`}>Select</button>
											</li>
										))}
									</ul>
								)}
							</section>

							<section className="ab-table" aria-label="Recent A/B Tests">
								<h2>Recent Tests</h2>
								{tests.length === 0 ? (
									<div className="ab-empty">No A/B tests found. Start your first test to see results here!</div>
								) : (
											<div className="ab-table-scroll">
												<table>
											<thead>
												<tr>
													<th>Name</th>
													<th>Status</th>
													<th>Start Date</th>
													<th>End Date</th>
													<th>Variants</th>
													<th>Action</th>
												</tr>
											</thead>
											<tbody>
												{tests.map(test => (
													<tr key={test.id}>
														<td>{test.name}</td>
														<td>{test.status}</td>
														<td>{test.startDate}</td>
														<td>{test.endDate || '-'}</td>
														<td>
															{test.variants && test.variants.length > 0 ? (
																test.variants.map(variant => (
																	<div key={variant.id}>
																		<strong>{variant.name}</strong>: {variant.conversionRate * 100}% ({variant.users} users)
																	</div>
																))
															) : (
																<span>No variants</span>
															)}
														</td>
														<td>
															<button onClick={() => onTestSelect(Number(test.id))} className="ab-select-btn" aria-label={`Select test ${test.name}`}>Select</button>
														</td>
													</tr>
												))}
											</tbody>
										</table>
										{hasMore && (
											<div className="ab-loadmore-container">
												<button
													className="ab-loadmore-btn"
													onClick={fetchMore}
													disabled={isFetchingMore}
													aria-label="Load more A/B tests"
												>
													{isFetchingMore ? 'Loading more...' : 'Load More'}
												</button>
											</div>
										)}
									</div>
								)}
							</section>
					</>
				)}
			</div>
		);
};

export default ABTestingDashboard;

