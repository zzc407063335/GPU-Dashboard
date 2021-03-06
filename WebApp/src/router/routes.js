import DashboardLayout from "@/layout/dashboard/DashboardLayout.vue";
// GeneralViews
import NotFound from "@/pages/NotFoundPage.vue";

// Admin pages
import Dashboard from "@/pages/Dashboard.vue";
// import UserProfile from "@/pages/UserProfile.vue";
// import Notifications from "@/pages/Notifications.vue";
// import Icons from "@/pages/Icons.vue";
// import Typography from "@/pages/Typography.vue";
import TableList from "@/pages/TableList.vue";

const routes = [
  {
    path: "/",
    component: DashboardLayout,
    redirect: "/dashboard",
    children: [
      {
        path: "dashboard",
        name: "dashboard",
        component: Dashboard,
        meta: {
            keepAlive: true // 需要被缓存
        }
      },
      // {
      //   path: "stats",
      //   name: "stats",
      //   component: UserProfile,
      // },
      // {
      //   path: "notifications",
      //   name: "notifications",
      //   component: Notifications,
      // },
      // {
      //   path: "icons",
      //   name: "icons",
      //   component: Icons,
      // },
      // {
      //   path: "typography",
      //   name: "typography",
      //   component: Typography,
      // },
      {
        path: "process-list",
        name: "process-list",
        component: TableList,
        meta: {
            keepAlive: true // 需要被缓存
        }
      }
    ]
  },
  { path: "*", component: NotFound }
];

/**
 * Asynchronously load view (Webpack Lazy loading compatible)
 * The specified component must be inside the Views folder
 * @param  {string} name  the filename (basename) of the view to load.
function view(name) {
   var res= require('../components/Dashboard/Views/' + name + '.vue');
   return res;
};**/

export default routes;
