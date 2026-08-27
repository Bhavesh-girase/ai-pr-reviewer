import { useMutation, useQueryClient } from '@tanstack/react-query'
import { reviewPullRequest } from '@/api/review'
import { type ReviewFormValues, type ReviewResponse } from '@/types/review'
import { toast } from 'sonner'

export function useReviewMutation() {
  const queryClient = useQueryClient()

  return useMutation<ReviewResponse, Error, ReviewFormValues>({
    mutationFn: reviewPullRequest,
    onMutate: (variables) => {
      // Display a persistent toast during the analysis
      toast.loading(`Analyzing PR #${variables.pullNumber} on ${variables.owner}/${variables.repo}...`, {
        id: 'review-pr',
      })
    },
    onSuccess: (data, variables) => {
      toast.success('Pull request analyzed successfully!', {
        id: 'review-pr',
        description: `Retrieved AI review suggestions for ${variables.owner}/${variables.repo}.`,
      })
      // Cache the result for subsequent dashboards or details queries
      queryClient.setQueryData(['active-review'], data)
      localStorage.setItem('active-review', JSON.stringify(data))
      localStorage.setItem('active-review-meta', JSON.stringify({
        owner: variables.owner,
        repo: variables.repo,
        pullNumber: variables.pullNumber,
        baseBranch: data.metadata?.base_branch || 'main',
        headBranch: data.metadata?.head_branch || 'feature'
      }))
    },
    onError: (error) => {
      toast.error('Review submission failed', {
        id: 'review-pr',
        description: error.message,
      })
    },
  })
}
