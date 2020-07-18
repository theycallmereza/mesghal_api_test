from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Category, Post

from ..serializers import PostSerializer

POST_URL = reverse('blog:post-list')


def detail_url(post_id):
    """Return post detail URL"""
    return reverse('blog:post-detail', args=[post_id])


def sample_category(name='Category Test'):
    """Create and return a sample category"""
    return Category.objects.create(name=name)


def sample_post(category, **params):
    """Create and return sample post"""
    defaults = {
        'title': 'Post Title',
        'content': 'Some Text ...',
    }
    defaults.update(params)

    return Post.objects.create(category=category, **defaults)


class PostTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_retrieve_posts(self):
        """Test retrieving list of posts"""
        category = sample_category()
        sample_post(category)
        sample_post(category)

        response = self.client.get(POST_URL)

        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_post_detail_view(self):
        """Test viewing post detail"""
        post = sample_post(sample_category())

        url = detail_url(post.id)
        response = self.client.get(url)
        serializer = PostSerializer(post)

        self.assertEqual(response.data, serializer.data)

    def test_create_post(self):
        """Test creating post"""
        payload = {
            'title': 'Post One',
            'content': 'Some Text ...',
            'category': sample_category().id,
        }

        response = self.client.post(POST_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        post = Post.objects.get(id=response.data['id'])
        for key in payload.keys():
            if key == 'category':
                self.assertEqual(payload[key], getattr(post, key).id)
            else:
                self.assertEqual(payload[key], getattr(post, key))

    def test_partial_update_post(self):
        """Test updating post with PATCH"""
        post = sample_post(sample_category())
        category = sample_category('Update Category')
        payload = {
            'title': 'Update Title',
            'category': category.id
        }

        url = detail_url(post.id)
        self.client.patch(url, payload)

        post.refresh_from_db()

        self.assertEqual(post.title, payload['title'])
        self.assertEqual(post.category.id, payload['category'])

    def test_full_update_post(self):
        """Test updating post with PUT"""
        post = sample_post(sample_category())

        payload = {
            'title': 'Update Title',
            'content': 'Update Content',
            'status': False,
            'category': sample_category('Update Category').id
        }

        url = detail_url(post.id)
        self.client.put(url, payload)

        post.refresh_from_db()

        self.assertEqual(post.title, payload['title'])
        self.assertEqual(post.content, payload['content'])
        self.assertEqual(post.status, payload['status'])
        self.assertEqual(post.category.id, payload['category'])

    def test_retrieve_post_with_status_true(self):
        """Test filtering posts with status true"""
        category = sample_category()
        post1 = sample_post(category)
        post2 = sample_post(category, status=False)

        response = self.client.get(POST_URL, {'status': 1})

        serializer1 = PostSerializer(post1)
        serializer2 = PostSerializer(post2)

        self.assertNotIn(serializer2.data, response.data)
        self.assertIn(serializer1.data, response.data)

    def test_search_posts(self):
        """Test searching posts with a query"""
        category = sample_category()
        post1 = sample_post(category, title="Post One")
        post2 = sample_post(category, title="Post Two")

        response = self.client.get(POST_URL, {'search': 'One'})

        serializer1 = PostSerializer(post1)
        serializer2 = PostSerializer(post2)

        self.assertIn(serializer1.data, response.data)
        self.assertNotIn(serializer2.data, response.data)

    def test_ordering_posts(self):
        """Test ordering posts with fields"""
        category = sample_category()
        post2 = sample_post(category, title='BBB')
        post3 = sample_post(category, title='BBB')
        post1 = sample_post(category, title='AAA')

        response = self.client.get(POST_URL, {'ordering': 'title,-cdt'})

        serializer1 = PostSerializer(post1)
        serializer2 = PostSerializer(post2)
        serializer3 = PostSerializer(post3)

        self.assertEqual(response.data[0], serializer1.data)
        self.assertEqual(response.data[1], serializer3.data)
        self.assertEqual(response.data[2], serializer2.data)