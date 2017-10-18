
console.log('Loading Centrify WebUI');

(function() {

function CentrifySideConfigController($scope, MinemeldConfigService, MineMeldRunningConfigStatusService,
                                  toastr, $modal, ConfirmService, $timeout) {
    var vm = this;

    // side config settings
    vm.centrify_user = undefined;
    vm.centrify_password = undefined;
    vm.centrify_tenant = undefined;
    
    vm.auth_timeout = undefined;
    vm.quarantine_role = undefined;

    vm.loadSideConfig = function() {
        var nodename = $scope.$parent.vm.nodename;

        MinemeldConfigService.getDataFile(nodename + '_side_config')
        .then((result) => {
            if (!result) {
                return;
            }

            if (result.centrify_user) {
                vm.centrify_user = result.centrify_user;
            } else {
                vm.centrify_user = undefined;
            }

            if (result.centrify_password) {
                vm.centrify_password = result.centrify_password;
            } else {
                vm.centrify_password = undefined;
            }

            if (result.centrify_tenant) {
                vm.centrify_tenant = result.centrify_tenant;
            } else {
                vm.centrify_tenant = undefined;
            }

            if (result.quarantine_role) {
                vm.quarantine_role = result.quarantine_role;
            } else {
                vm.quarantine_role = undefined;
            }

            if (result.auth_timeout) {
                vm.auth_timeout = result.auth_timeout;
            } else {
                vm.auth_timeout = undefined;
            }


        }, (error) => {
            toastr.error('ERROR RETRIEVING NODE SIDE CONFIG: ' + error.status);
            vm.centrify_user = undefined;
            vm.centrify_password = undefined;
            vm.centrify_tenant = undefined;
            vm.quarantine_role = undefined;
            vm.auth_timeout  = undefined;
        })
        .finally();
    };

    vm.saveSideConfig = function() {
        var side_config = {};
        var nodename = $scope.$parent.vm.nodename;

        if (vm.centrify_user) {
            side_config.centrify_user = vm.centrify_user;
        }

        if (vm.centrify_password) {
            side_config.centrify_password = vm.centrify_password;
        }

        if (vm.centrify_tenant) {
            side_config.centrify_tenant = vm.centrify_tenant;
        }

        if (vm.auth_timeout) {
            side_config.auth_timeout = vm.auth_timeout;
        }

        if (vm.quarantine_role) {
            side_config.quarantine_role = vm.quarantine_role;
        }

        return MinemeldConfigService.saveDataFile(
            nodename + '_side_config',
            side_config,
            nodename
        );
    };

   vm.setCentrifyUser = function() {
        var mi = $modal.open({
            templateUrl: '/extensions/webui/mmcentrifyWebui/centrify.output.apiuser.html',
            controller: ['$modalInstance', CentrifyUserController],
            controllerAs: 'vm',
            bindToController: true,
            backdrop: 'static',
            animation: false
        });

        mi.result.then((result) => {
            vm.centrify_user = result.centrify_user;

            return vm.saveSideConfig();
        })
        .then((result) => {
            toastr.success('API USER SET');
            vm.loadSideConfig();
        }, (error) => {
            toastr.error('ERROR SETTING API USER: ' + error.statusText);
        });
    };

    vm.setCentrifyPassword = function() {
        var mi = $modal.open({
            templateUrl: '/extensions/webui/mmcentrifyWebui/centrify.output.apipassword.html',
            controller: ['$modalInstance', CentrifyPasswordController],
            controllerAs: 'vm',
            bindToController: true,
            backdrop: 'static',
            animation: false
        });

        mi.result.then((result) => {
            vm.centrify_password = result.centrify_password;

            return vm.saveSideConfig();
        })
        .then((result) => {
            toastr.success('API PASSWORD SET');
            vm.loadSideConfig();
        }, (error) => {
            toastr.error('ERROR SETTING API PASSWORD: ' + error.statusText);
        });
    };

   vm.setCentrifyTenant = function() {
        var mi = $modal.open({
            templateUrl: '/extensions/webui/mmcentrifyWebui/centrify.output.tenant.html',
            controller: ['$modalInstance', CentrifyTenantController],
            controllerAs: 'vm',
            bindToController: true,
            backdrop: 'static',
            animation: false
        });

        mi.result.then((result) => {
            vm.centrify_tenant = result.centrify_tenant;

            return vm.saveSideConfig();
        })
        .then((result) => {
            toastr.success('CENTRIFY TENANT SET');
            vm.loadSideConfig();
        }, (error) => {
            toastr.error('ERROR SETTING CENTRIFY TENANT: ' + error.statusText);
        });
    };

   vm.setQuarantineRole = function() {

        var mi = $modal.open({
            templateUrl: '/extensions/webui/mmcentrifyWebui/centrify.output.quarantinerole.html',
            controller: ['$modalInstance', CentrifyQuarantineRoleController],
            controllerAs: 'vm',
            bindToController: true,
            backdrop: 'static',
            animation: false
        });

        mi.result.then((result) => {
            vm.quarantine_role = result.quarantine_role;

            return vm.saveSideConfig();
        })
        .then((result) => {
            toastr.success('QUARANTINE ROLE SET');
            vm.loadSideConfig();
        }, (error) => {
            toastr.error('ERROR SETTING QUARANTINE ROLE: ' + error.statusText);
        });
    };

    vm.setAuthTimeout = function() {

        var mi = $modal.open({
            templateUrl: '/extensions/webui/mmcentrifyWebui/centrify.output.authtimeout.html',
            controller: ['$modalInstance', CentrifyAuthTimeoutController],
            controllerAs: 'vm',
            bindToController: true,
            backdrop: 'static',
            animation: false
        });

        mi.result.then((result) => {
            vm.auth_timeout = result.auth_timeout;

            return vm.saveSideConfig();
        })
        .then((result) => {
            toastr.success('AUTH TIMEOUT SET');
            vm.loadSideConfig();
        }, (error) => {
            toastr.error('ERROR SETTING AUTH TIMEOUT: ' + error.statusText);
        });
    };


    vm.loadSideConfig();
}

function CentrifyUserController($modalInstance) {
    var vm = this;

    vm.centrify_user = undefined;
    
    vm.valid = function() {
        if (!vm.centrify_user) {
            return false;
        }

        return true;
    };

    vm.save = function() {
        var result = {};

        result.centrify_user = vm.centrify_user;

        $modalInstance.close(result);
    }

    vm.cancel = function() {
        $modalInstance.dismiss();
    }
}

function CentrifyPasswordController($modalInstance) {
    var vm = this;

    vm.centrify_password = undefined;
    vm.centrify_password2 = undefined;

    vm.valid = function() {
        if (vm.centrify_password !== vm.centrify_password2) {
            angular.element('#fgCentrifyPassword1').addClass('has-error');
            angular.element('#fgCentrifyPassword2').addClass('has-error');

            return false;
        }
        angular.element('#fgCentrifyPassword1').removeClass('has-error');
        angular.element('#fgCentrifyPassword2').removeClass('has-error');

        if (!vm.centrify_password) {
            return false;
        }

        return true;
    };

    vm.save = function() {
        var result = {};

        result.centrify_password = vm.centrify_password2;

        $modalInstance.close(result);
    }

    vm.cancel = function() {
        $modalInstance.dismiss();
    }
}

function CentrifyTenantController($modalInstance) {
    var vm = this;

    vm.centrify_tenant = undefined;
    
    vm.valid = function() {
        if (!vm.centrify_tenant) {
            return false;
        }

        return true;
    };

    vm.save = function() {
        var result = {};

        result.centrify_tenant = vm.centrify_tenant;

        $modalInstance.close(result);
    }

    vm.cancel = function() {
        $modalInstance.dismiss();
    }
}

function CentrifyQuarantineRoleController($modalInstance) {
    var vm = this;

    vm.quarantine_role = undefined;
    
    vm.valid = function() {
        if (!vm.quarantine_role) {
            return false;
        }

        return true;
    };

    vm.save = function() {
        var result = {};

        result.quarantine_role = vm.quarantine_role;

        $modalInstance.close(result);
    }

    vm.cancel = function() {
        $modalInstance.dismiss();
    }
}

function CentrifyAuthTimeoutController($modalInstance) {
    var vm = this;

    vm.auth_timeout = undefined;
    
    vm.valid = function() {
        if (!vm.auth_timeout) {
            return false;
        }
        if(!isInteger(vm.auth_timeout)) {
            return false;
        }

        return true;
    };

    vm.save = function() {
        var result = {};

        result.auth_timeout = vm.auth_timeout

        $modalInstance.close(result);
    }

    vm.cancel = function() {
        $modalInstance.dismiss();
    }
}

angular.module('mmcentrifyWebui', [])
    .controller('CentrifySideConfigController', [
        '$scope', 'MinemeldConfigService', 'MineMeldRunningConfigStatusService',
        'toastr', '$modal', 'ConfirmService', '$timeout',
        CentrifySideConfigController
    ])
    .config(['$stateProvider', function($stateProvider) {
        $stateProvider.state('nodedetail.centrifyinfo', {
            templateUrl: '/extensions/webui/mmcentrifyWebui/centrify.output.info.html',
            controller: 'NodeDetailInfoController',
            controllerAs: 'vm'
        });
    }])
    .run(['NodeDetailResolver', '$state', function(NodeDetailResolver, $state) {
        NodeDetailResolver.registerClass('mmcentrify.node.CentrifyOutput', {
            tabs: [{
                icon: 'fa fa-circle-o',
                tooltip: 'INFO',
                state: 'nodedetail.centrifyinfo',
                active: false
            },
            {
                icon: 'fa fa-area-chart',
                tooltip: 'STATS',
                state: 'nodedetail.stats',
                active: false
            },
            {
                icon: 'fa fa-asterisk',
                tooltip: 'GRAPH',
                state: 'nodedetail.graph',
                active: false
            }]
        });

        // if a nodedetail is already shown, reload the current state to apply changes
        // we should definitely find a better way to handle this...
        if ($state.$current.toString().startsWith('nodedetail.')) {
            $state.reload();
        }
    }]);
})();